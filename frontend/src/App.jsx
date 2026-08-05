import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ChatRoom from './pages/ChatRoom'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-atmosphere" aria-hidden="true" />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/rooms/:roomSlug" element={<ChatRoom />} />
      </Routes>
    </BrowserRouter>
  )
}
