"""
Confidence Calibration module.

Implements calibration techniques to improve the reliability of
LLM confidence scores and prediction probabilities.

Key techniques:
- Platt Scaling: Logistic regression on LLM logits
- Temperature Scaling: Single parameter post-hoc calibration
- Isotonic Regression: Non-parametric calibration
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class CalibrationResult:
    """Result of applying calibration to a confidence score."""
    
    original_confidence: float
    calibrated_confidence: float
    calibration_method: str
    uncertainty_interval: tuple[float, float]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "original": self.original_confidence,
            "calibrated": self.calibrated_confidence,
            "method": self.calibration_method,
            "uncertainty_low": self.uncertainty_interval[0],
            "uncertainty_high": self.uncertainty_interval[1],
        }


class TemperatureScaler:
    """
    Temperature scaling for LLM confidence calibration.
    
    Applies a single temperature parameter T to soften or sharpen
    the confidence distribution: calibrated = sigmoid(logit(conf) / T)
    
    Lower T (< 1) = sharper, more confident
    Higher T (> 1) = softer, less confident
    """
    
    def __init__(self, temperature: float = 1.5):
        """
        Initialize with temperature parameter.
        
        Args:
            temperature: T parameter. Default 1.5 assumes LLMs are overconfident.
        """
        self.temperature = temperature
        self._fitted = False
    
    def _logit(self, p: float) -> float:
        """Convert probability to logit."""
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return np.log(p / (1 - p))
    
    def _sigmoid(self, x: float) -> float:
        """Convert logit to probability."""
        return 1 / (1 + np.exp(-x))
    
    def calibrate(self, confidence: float) -> CalibrationResult:
        """
        Apply temperature scaling to a confidence score.
        
        Args:
            confidence: Original confidence score (0-1)
        
        Returns:
            CalibrationResult with adjusted confidence
        """
        logit = self._logit(confidence)
        scaled_logit = logit / self.temperature
        calibrated = self._sigmoid(scaled_logit)
        
        # Calculate uncertainty interval (±10% of calibrated value)
        uncertainty_margin = 0.1 * calibrated
        interval = (
            max(0, calibrated - uncertainty_margin),
            min(1, calibrated + uncertainty_margin)
        )
        
        return CalibrationResult(
            original_confidence=confidence,
            calibrated_confidence=calibrated,
            calibration_method="temperature_scaling",
            uncertainty_interval=interval,
        )
    
    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        """
        Fit temperature parameter using validation data.
        
        Minimizes negative log likelihood on validation set.
        
        Args:
            confidences: Predicted confidence scores
            outcomes: Actual binary outcomes (True = correct prediction)
        """
        from scipy.optimize import minimize_scalar
        
        def nll(T: float) -> float:
            """Negative log likelihood for temperature T."""
            calibrated = [self._sigmoid(self._logit(c) / T) for c in confidences]
            eps = 1e-7
            ll = sum(
                o * np.log(c + eps) + (1 - o) * np.log(1 - c + eps)
                for c, o in zip(calibrated, outcomes)
            )
            return -ll
        
        result = minimize_scalar(nll, bounds=(0.1, 10.0), method='bounded')
        self.temperature = result.x
        self._fitted = True
        logger.info(f"Temperature scaling fitted: T={self.temperature:.3f}")


class PlattScaler:
    """
    Platt scaling using logistic regression.
    
    Fits parameters A and B such that:
    calibrated = sigmoid(A * logit(conf) + B)
    
    More flexible than temperature scaling, can correct both
    over/under-confidence and shift the decision boundary.
    """
    
    def __init__(self):
        self.A = 1.0
        self.B = 0.0
        self._fitted = False
    
    def _logit(self, p: float) -> float:
        """Convert probability to logit."""
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return np.log(p / (1 - p))
    
    def _sigmoid(self, x: float) -> float:
        """Convert logit to probability."""
        return 1 / (1 + np.exp(-np.clip(x, -700, 700)))
    
    def calibrate(self, confidence: float) -> CalibrationResult:
        """
        Apply Platt scaling to a confidence score.
        
        Args:
            confidence: Original confidence score (0-1)
        
        Returns:
            CalibrationResult with adjusted confidence
        """
        logit = self._logit(confidence)
        scaled_logit = self.A * logit + self.B
        calibrated = self._sigmoid(scaled_logit)
        
        # Uncertainty based on how far from 0.5 (more uncertain near boundaries)
        distance_from_half = abs(calibrated - 0.5)
        uncertainty_margin = 0.15 * (1 - distance_from_half)
        interval = (
            max(0, calibrated - uncertainty_margin),
            min(1, calibrated + uncertainty_margin)
        )
        
        return CalibrationResult(
            original_confidence=confidence,
            calibrated_confidence=calibrated,
            calibration_method="platt_scaling",
            uncertainty_interval=interval,
        )
    
    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        """
        Fit Platt scaling parameters using logistic regression.
        
        Args:
            confidences: Predicted confidence scores
            outcomes: Actual binary outcomes
        """
        try:
            from sklearn.linear_model import LogisticRegression
            
            # Convert to logits
            X = np.array([[self._logit(c)] for c in confidences])
            y = np.array([1 if o else 0 for o in outcomes])
            
            # Fit logistic regression
            model = LogisticRegression(solver='lbfgs', max_iter=1000)
            model.fit(X, y)
            
            self.A = model.coef_[0][0]
            self.B = model.intercept_[0]
            self._fitted = True
            
            logger.info(f"Platt scaling fitted: A={self.A:.3f}, B={self.B:.3f}")
            
        except ImportError:
            logger.warning("sklearn not available, using default Platt parameters")
        except Exception as e:
            logger.error(f"Platt scaling fit failed: {e}")


class IsotonicCalibrator:
    """
    Isotonic regression calibration.
    
    Non-parametric calibration that preserves ordering while
    making the calibration curve monotonically increasing.
    """
    
    def __init__(self):
        self._model = None
        self._fitted = False
    
    def calibrate(self, confidence: float) -> CalibrationResult:
        """Apply isotonic calibration."""
        if self._fitted and self._model is not None:
            calibrated = float(self._model.predict([[confidence]])[0])
        else:
            # Default: slight reduction for overconfident LLMs
            calibrated = confidence * 0.85
        
        calibrated = np.clip(calibrated, 0, 1)
        
        interval = (
            max(0, calibrated - 0.1),
            min(1, calibrated + 0.1)
        )
        
        return CalibrationResult(
            original_confidence=confidence,
            calibrated_confidence=calibrated,
            calibration_method="isotonic_regression",
            uncertainty_interval=interval,
        )
    
    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        """Fit isotonic regression model."""
        try:
            from sklearn.isotonic import IsotonicRegression
            
            X = np.array(confidences)
            y = np.array([1.0 if o else 0.0 for o in outcomes])
            
            self._model = IsotonicRegression(out_of_bounds='clip')
            self._model.fit(X, y)
            self._fitted = True
            
            logger.info("Isotonic calibration fitted")
            
        except ImportError:
            logger.warning("sklearn not available for isotonic calibration")


class ConfidenceCalibrator:
    """
    Main calibration interface combining multiple methods.
    
    Provides a unified API for calibrating LLM confidence scores
    with support for multiple calibration strategies.
    """
    
    def __init__(
        self,
        method: str = "temperature",
        temperature: float = 1.5,
    ):
        """
        Initialize calibrator.
        
        Args:
            method: "temperature", "platt", or "isotonic"
            temperature: Temperature for temperature scaling
        """
        self.method = method
        
        if method == "temperature":
            self._calibrator = TemperatureScaler(temperature)
        elif method == "platt":
            self._calibrator = PlattScaler()
        elif method == "isotonic":
            self._calibrator = IsotonicCalibrator()
        else:
            raise ValueError(f"Unknown calibration method: {method}")
    
    def calibrate(self, confidence: float) -> CalibrationResult:
        """
        Calibrate a single confidence score.
        
        Args:
            confidence: Original confidence (0-1)
        
        Returns:
            CalibrationResult with calibrated confidence and uncertainty
        """
        return self._calibrator.calibrate(confidence)
    
    def calibrate_batch(self, confidences: list[float]) -> list[CalibrationResult]:
        """Calibrate a batch of confidence scores."""
        return [self.calibrate(c) for c in confidences]
    
    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        """
        Fit calibrator on validation data.
        
        Args:
            confidences: Predicted confidence scores
            outcomes: Actual outcomes (True = correct)
        """
        self._calibrator.fit(confidences, outcomes)
    
    def expected_calibration_error(
        self, 
        confidences: list[float], 
        outcomes: list[bool],
        n_bins: int = 10
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        
        Lower ECE = better calibration.
        
        Args:
            confidences: Predicted confidences
            outcomes: Actual outcomes
            n_bins: Number of bins for calibration
        
        Returns:
            ECE score (0-1, lower is better)
        """
        # Calibrate first
        calibrated = [self.calibrate(c).calibrated_confidence for c in confidences]
        
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        total = len(confidences)
        
        for i in range(n_bins):
            bin_mask = [(bins[i] <= c < bins[i+1]) for c in calibrated]
            bin_count = sum(bin_mask)
            
            if bin_count > 0:
                bin_conf = np.mean([c for c, m in zip(calibrated, bin_mask) if m])
                bin_acc = np.mean([o for o, m in zip(outcomes, bin_mask) if m])
                ece += (bin_count / total) * abs(bin_acc - bin_conf)
        
        return ece


def get_default_calibrator() -> ConfidenceCalibrator:
    """Get a default calibrator with sensible settings for LLMs."""
    return ConfidenceCalibrator(method="temperature", temperature=1.5)


# Module-level singleton
_calibrator: Optional[ConfidenceCalibrator] = None


def get_calibrator() -> ConfidenceCalibrator:
    """Get the global calibrator singleton."""
    global _calibrator
    if _calibrator is None:
        _calibrator = get_default_calibrator()
    return _calibrator
