import { WarningIcon } from "./icons";

export default function Disclaimer() {
  return (
    <div className="disclaimer">
      <WarningIcon size={16} /> Visaroo shares general information and community
      experiences — this is <strong>not legal advice</strong>. Always verify with your
      DSO or an immigration attorney.
    </div>
  );
}
