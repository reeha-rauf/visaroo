import { Navigate, Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import { useAuth } from "./context/AuthContext";
import AskFab from "./components/AskFab";
import AskPanel from "./components/AskPanel";
import CountdownDock from "./components/CountdownDock";
import AttorneyHelpPage from "./pages/AttorneyHelpPage";
import CreatorFeedPage from "./pages/CreatorFeedPage";
import DeadlineTrackerPage from "./pages/DeadlineTrackerPage";
import Feed from "./pages/Feed";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import MyPostsPage from "./pages/MyPostsPage";
import NewPost from "./pages/NewPost";
import News from "./pages/News";
import Onboarding from "./pages/Onboarding";
import PostDetail from "./pages/PostDetail";
import Profile from "./pages/Profile";
import Search from "./pages/Search";
import Signup from "./pages/Signup";
import WebinarsPage from "./pages/WebinarsPage";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

/** Home route: Landing page when logged out, the community Feed when logged in. */
function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading…</div>;
  return user ? <Feed /> : <Landing />;
}

export default function App() {
  return (
    <>
      <NavBar />
      <AskPanel />
      <AskFab />
      <CountdownDock />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/news" element={<News />} />
        <Route
          path="/webinars"
          element={
            <RequireAuth>
              <WebinarsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/feed"
          element={
            <RequireAuth>
              <CreatorFeedPage />
            </RequireAuth>
          }
        />
        <Route
          path="/legal-help"
          element={
            <RequireAuth>
              <AttorneyHelpPage />
            </RequireAuth>
          }
        />
        <Route path="/posts/:id" element={<PostDetail />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/new"
          element={
            <RequireAuth>
              <NewPost />
            </RequireAuth>
          }
        />
        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          path="/deadlines"
          element={
            <RequireAuth>
              <DeadlineTrackerPage />
            </RequireAuth>
          }
        />
        <Route
          path="/my-posts"
          element={
            <RequireAuth>
              <MyPostsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
      </Routes>
    </>
  );
}
