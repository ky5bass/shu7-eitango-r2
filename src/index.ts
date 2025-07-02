/**
 * Shows how to restrict access using the HTTP Basic schema.
 * @see https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
 * @see https://tools.ietf.org/html/rfc7617
 *
 * A user-id containing a colon (":") character is invalid, as the
 * first colon in a user-pass string separates user and password.
 */

import { getAssetFromKV } from "@cloudflare/kv-asset-handler";
import manifestJSON from "__STATIC_CONTENT_MANIFEST";
const assetManifest = JSON.parse(manifestJSON);
/* 参考 https://developers.cloudflare.com/workers/configuration/sites/start-from-worker/ */

interface Env {
  __STATIC_CONTENT: KVNamespace<string>;
};

/**
 * Receives a HTTP request and replies with a response.
 * @param {Request} request
 * @returns {Promise<Response>}
*/
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {

    /* 公開ディレクトリのコンテンツを返す                                                    */
    /* 参考 https://developers.cloudflare.com/workers/configuration/sites/start-from-worker/ */
    try {
      return await getAssetFromKV(
        {
          request,
          waitUntil: ctx.waitUntil.bind(ctx),
        },
        {
          ASSET_NAMESPACE: env.__STATIC_CONTENT,
          ASSET_MANIFEST: assetManifest,
        },
      );
    } catch (e) {
      let pathname = new URL(request.url).pathname;
      return new Response(`"${pathname}" not found`, {
        status: 404,
        statusText: "not found",
      });
    }

  },
} satisfies ExportedHandler<Env>;