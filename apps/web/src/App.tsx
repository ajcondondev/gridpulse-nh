import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './routes/Dashboard'
import { DatasetDetailPage } from './routes/DatasetDetailPage'
import { DatasetsPage } from './routes/DatasetsPage'
import { SourceDetailPage } from './routes/SourceDetailPage'
import { SourcesPage } from './routes/SourcesPage'
import { WeatherDemandPage } from './routes/WeatherDemandPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'sources', element: <SourcesPage /> },
      { path: 'sources/:sourceId', element: <SourceDetailPage /> },
      { path: 'datasets', element: <DatasetsPage /> },
      { path: 'datasets/:datasetId', element: <DatasetDetailPage /> },
      { path: 'analysis/weather-demand', element: <WeatherDemandPage /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
