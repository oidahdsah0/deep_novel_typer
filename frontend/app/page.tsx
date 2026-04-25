import { LibraryClient } from "@/app/library-client";
import { getLibrarySnapshot } from "@/lib/api/index";

export default async function Home() {
  const library = await getLibrarySnapshot();

  return <LibraryClient initialLibrary={library} />;
}
