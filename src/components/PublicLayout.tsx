import { Outlet } from "react-router-dom";
import SiteFooter from "./SiteFooter";
import FloatingActions from "./FloatingActions";

export default function PublicLayout() {
  return (
    <>
      <Outlet />
      <SiteFooter />
      <FloatingActions />
    </>
  );
}
