import { Link } from "react-router-dom";

type BrandProps = {
  light?: boolean;
};

export default function Brand({ light = false }: BrandProps) {
  return (
    <Link
      className={`brand${light ? " brand--light" : ""}`}
      to="/"
      aria-label="ALMASI home"
    >
      <span className="brand__mark" aria-hidden="true">
        A
      </span>
      <span className="brand__name">ALMASI</span>
    </Link>
  );
}
