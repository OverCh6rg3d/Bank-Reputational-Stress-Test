import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import { SimulationProvider } from './context/SimulationContext';

function App() {
  return (
    <SimulationProvider>
      <Layout>
        <Dashboard />
      </Layout>
    </SimulationProvider>
  )
}

export default App
