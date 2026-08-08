// エントリポイント。ルート表(router.js の ROUTES)を登録してルーターを起動する(P002 2.2)。

import * as router from './lib/router.js';

router.defineDefaultRoutes();

if (globalThis.document) {
  router.start();
}
