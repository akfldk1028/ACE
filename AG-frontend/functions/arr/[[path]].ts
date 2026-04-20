// CF Pages Function: proxy /arr/* → AG-light Worker
const WORKER_URL = "https://law-light-api.clickaround8.workers.dev";

export const onRequest: PagesFunction = async (context) => {
  const url = new URL(context.request.url);
  const path = url.pathname.replace(/^\/arr/, "");
  const target = `${WORKER_URL}${path}${url.search}`;

  const headers = new Headers(context.request.headers);
  headers.set("Origin", "http://localhost");
  headers.set("Referer", "http://localhost");

  return fetch(target, {
    method: context.request.method,
    headers,
    body: context.request.method !== "GET" ? context.request.body : undefined,
  });
};
