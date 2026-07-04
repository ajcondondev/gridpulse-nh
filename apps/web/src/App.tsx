import { Suspense, lazy } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Layout } from './components/Layout'

// Route-level code splitting: the story page loads first and stays light;
// the workbench (data explorer) pages ship in their own chunks.
const StoryPage = lazy(() => import('./story/StoryPage'))
const Dashboard = lazy(() =>
  import('./routes/Dashboard').then((m) => ({ default: m.Dashboard })),
)
const SourcesPage = lazy(() =>
  import('./routes/SourcesPage').then((m) => ({ default: m.SourcesPage })),
)
const SourceDetailPage = lazy(() =>
  import('./routes/SourceDetailPage').then((m) => ({ default: m.SourceDetailPage })),
)
const DatasetsPage = lazy(() =>
  import('./routes/DatasetsPage').then((m) => ({ default: m.DatasetsPage })),
)
const DatasetDetailPage = lazy(() =>
  import('./routes/DatasetDetailPage').then((m) => ({ default: m.DatasetDetailPage })),
)
const WeatherDemandPage = lazy(() =>
  import('./routes/WeatherDemandPage').then((m) => ({ default: m.WeatherDemandPage })),
)

function page(element: React.ReactNode) {
  return (
    <Suspense
      fallback={<p className="text-sm text-slate-400 py-12 text-center">Loading…</p>}
    >
      {element}
    </Suspense>
  )
}

const router = createBrowserRouter(
  [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: page(<StoryPage />) },
      { path: 'explorer', element: page(<Dashboard />) },
      { path: 'sources', element: page(<SourcesPage />) },
      { path: 'sources/:sourceId', element: page(<SourceDetailPage />) },
      { path: 'datasets', element: page(<DatasetsPage />) },
      { path: 'datasets/:datasetId', element: page(<DatasetDetailPage />) },
      { path: 'analysis/weather-demand', element: page(<WeatherDemandPage />) },
    ],
  },
  ],
  // Follow Vite's base so the app works at / locally and under
  // /gridpulse-nh/ on GitHub Pages.
  { basename: import.meta.env.BASE_URL },
)

export default function App() {
  return <RouterProvider router={router} />
}
