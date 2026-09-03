const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const port = Number(process.env.PORT || 3040);
const root = __dirname;

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

const publicPaths = new Set([
  "index.html",
  "styles.css",
  "app.js",
  "fixture.js",
  "worlds.json",
  "receipts.json",
  "live_model_receipt.json",
  "assets/mark.svg",
  "assets/checkpoint.svg",
]);

const securityHeaders = {
  "Content-Security-Policy": [
    "default-src 'none'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "font-src 'self'",
    "connect-src 'self'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
    "object-src 'none'",
  ].join("; "),
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

const server = http.createServer((request, response) => {
  for (const [name, value] of Object.entries(securityHeaders)) response.setHeader(name, value);

  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end("Method not allowed");
    return;
  }

  const rawPath = (request.url || "/").split(/[?#]/, 1)[0] || "/";
  if (rawPath.includes("..") || rawPath.includes("\\")) {
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
  if (pathname.includes("..") || pathname.includes("\\") || pathname.includes("\0")) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  const relativePath = pathname === "/" ? "index.html" : pathname.replace(/^\/+/, "");
  if (!publicPaths.has(relativePath)) {
    response.writeHead(404);
    response.end("Not found");
    return;
  }

  const filePath = path.resolve(root, relativePath);
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
    response.writeHead(200, {
      "Content-Type": types[extension] || "application/octet-stream",
      // Filenames are intentionally stable. Revalidation prevents mixed-version
      // HTML, scripts, catalogs, and receipts after a deploy.
      "Cache-Control": "no-cache, max-age=0",
    });
    response.end(request.method === "HEAD" ? undefined : body);
  });
});

if (require.main === module) {
  server.listen(port, () => console.log(`bio claim firewall site listening on ${port}`));
}

module.exports = { publicPaths, securityHeaders, server };
