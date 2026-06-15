const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "host",
  "transfer-encoding",
]);

exports.handler = async (event) => {
  const backendUrl = process.env.BACKEND_URL;

  if (!backendUrl) {
    return jsonResponse(502, {
      detail:
        "BACKEND_URL is not set in Netlify. Set it to your deployed FastAPI backend URL.",
    });
  }

  const path = getApiPath(event.path);
  const query = event.rawQuery ? `?${event.rawQuery}` : "";
  const targetUrl = `${backendUrl.replace(/\/$/, "")}/api${path}${query}`;

  const headers = {};
  for (const [key, value] of Object.entries(event.headers || {})) {
    const normalizedKey = key.toLowerCase();
    if (!HOP_BY_HOP_HEADERS.has(normalizedKey)) {
      headers[key] = value;
    }
  }

  try {
    const response = await fetch(targetUrl, {
      method: event.httpMethod,
      headers,
      body:
        event.httpMethod === "GET" || event.httpMethod === "HEAD"
          ? undefined
          : Buffer.from(event.body || "", event.isBase64Encoded ? "base64" : "utf8"),
    });

    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
        responseHeaders[key] = value;
      }
    });

    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    return {
      statusCode: response.status,
      headers: responseHeaders,
      body: buffer.toString("base64"),
      isBase64Encoded: true,
    };
  } catch (error) {
    return jsonResponse(502, {
      detail: `Unable to reach backend API at ${targetUrl}: ${error.message}`,
    });
  }
};

function jsonResponse(statusCode, body) {
  return {
    statusCode,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  };
}

function getApiPath(path) {
  const directMatch = path.match(/^\/api\/?(.*)$/);
  if (directMatch) {
    return directMatch[1] ? `/${directMatch[1]}` : "";
  }

  const functionMatch = path.match(/^\/\.netlify\/functions\/api\/?(.*)$/);
  if (functionMatch) {
    return functionMatch[1] ? `/${functionMatch[1]}` : "";
  }

  return "";
}
