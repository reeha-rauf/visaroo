import MyContent from "../components/MyContent";

/** Standalone "My posts & answers" page (separate from profile settings). */
export default function MyPostsPage() {
  return (
    <div className="container">
      <div className="page-head">
        <h1>My Posts</h1>
        <p>Your questions and answers in the community.</p>
      </div>
      <MyContent heading={false} />
    </div>
  );
}
