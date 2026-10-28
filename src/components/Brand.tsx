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
      <img className="brand__logo" src="/almasi-logo.png" alt="ALMASI" />
    </Link>
  );
}
