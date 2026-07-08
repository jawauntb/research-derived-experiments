const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const port = Number(process.env.PORT || 3010);
const root = __dirname;

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

const server = http.createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end("Method not allowed");
    return;
  }

  const rawPath = (request.url || "/").split(/[?#]/, 1)[0] || "/";
  if (rawPath.includes("..")) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  let pathname;
  try {
    pathname = decodeURIComponent(rawPath);
  } catch {
    response.writeHead(400);
    response.end("Bad request");
    return;
  }
  if (pathname.includes("..")) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  const normalizedPath = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  if (!isPublicPath(normalizedPath)) {
    response.writeHead(404);
    response.end("Not found");
    return;
  }

  const filePath = path.resolve(root, normalizedPath);

  if (filePath !== root && !filePath.startsWith(`${root}${path.sep}`)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  fs.readFile(filePath, (error, body) => {
    if (error) {
      response.writeHead(404);
      response.end("Not found");
      return;
    }

    const extension = path.extname(filePath);
    const cacheControl = extension === ".html" ? "no-cache, max-age=0" : "public, max-age=300";
    response.writeHead(200, {
      "Content-Type": types[extension] || "application/octet-stream",
      "Cache-Control": cacheControl,
    });
    response.end(request.method === "HEAD" ? undefined : body);
  });
});

server.listen(port, () => {
  console.log(`inquiry black box site listening on ${port}`);
});

function isPublicPath(relativePath) {
  return (
    relativePath === "index.html" ||
    relativePath === "styles.css" ||
    relativePath === "app.js" ||
    relativePath === "assets/aperture-icon.png" ||
    relativePath === "assets/aperture-mark.png"
  );
}
