import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ChatPage from './pages/Chat';
import EvalPage from './pages/Eval';
import ArchitecturePage from './pages/Architecture';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ChatPage />} />
        <Route path="/eval" element={<EvalPage />} />
        <Route path="/architecture" element={<ArchitecturePage />} />
      </Route>
    </Routes>
  );
}
