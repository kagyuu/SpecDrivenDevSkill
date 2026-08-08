// U001-T5 単体テスト — api.js(P002 5.2 / 2.4)。fetch を差し替えて検証する。
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import * as api from '../src/lib/api.js';

let calls = [];
let navigations = [];

function stubFetch(status, payload) {
  api.runtime.fetch = async (path, options) => {
    calls.push({ path, options });
    return {
      status,
      json: async () => {
        if (payload === undefined) throw new Error('no body');
        return payload;
      },
    };
  };
}

beforeEach(() => {
  calls = [];
  navigations = [];
  api.runtime.navigate = (hash) => navigations.push(hash);
  api.takePendingMessage();
});

test('200: JSONを返し、同一オリジン・JSONヘッダで送る', async () => {
  stubFetch(200, { user: { user_id: 'user001' } });
  const result = await api.post('/api/auth/login', { user_id: 'user001' });
  assert.deepEqual(result, { user: { user_id: 'user001' } });
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].options.credentials, 'same-origin');
  assert.equal(calls[0].options.headers['Content-Type'], 'application/json');
  assert.equal(calls[0].options.body, JSON.stringify({ user_id: 'user001' }));
});

test('204: null を返す', async () => {
  stubFetch(204, undefined);
  assert.equal(await api.del('/api/rooms/1'), null);
});

test('400 VALIDATION_ERROR: details を持つエラーをthrowする', async () => {
  stubFetch(400, {
    error: {
      code: 'VALIDATION_ERROR',
      message: '入力内容に誤りがあります。',
      details: [{ field: 'user_id', message: 'ユーザーIDを入力してください。' }],
    },
  });
  await assert.rejects(
    () => api.post('/api/auth/login', {}),
    (err) => {
      assert.equal(err.status, 400);
      assert.equal(err.code, 'VALIDATION_ERROR');
      assert.equal(err.details[0].field, 'user_id');
      return true;
    }
  );
});

test('401 UNAUTHENTICATED: #/login へ遷移しセッション切れメッセージを残す', async () => {
  stubFetch(401, { error: { code: 'UNAUTHENTICATED', message: 'セッションの有効期限が切れました。再度ログインしてください。' } });
  await assert.rejects(() => api.get('/api/me'));
  assert.deepEqual(navigations, ['#/login']);
  assert.equal(api.takePendingMessage(), api.SESSION_EXPIRED_MESSAGE);
  assert.equal(api.takePendingMessage(), null);
});

test('401 AUTH_FAILED: 遷移しない(S01が自分で表示する)', async () => {
  stubFetch(401, { error: { code: 'AUTH_FAILED', message: 'ユーザーIDまたはパスワードが正しくありません。' } });
  await assert.rejects(
    () => api.post('/api/auth/login', {}),
    (err) => err.code === 'AUTH_FAILED' && err.status === 401
  );
  assert.deepEqual(navigations, []);
});

test('403 / 404: コードとメッセージをそのまま持つ', async () => {
  stubFetch(403, { error: { code: 'FORBIDDEN', message: 'この操作を行う権限がありません。' } });
  await assert.rejects(() => api.get('/api/users'), (err) => err.status === 403 && err.code === 'FORBIDDEN');
  stubFetch(404, { error: { code: 'NOT_FOUND', message: '対象のデータが見つかりません。削除された可能性があります。' } });
  await assert.rejects(() => api.get('/api/rooms/99'), (err) => err.status === 404 && err.code === 'NOT_FOUND');
});

test('409 RESERVATION_CONFLICT: extra に conflicts を持つ', async () => {
  stubFetch(409, {
    error: {
      code: 'RESERVATION_CONFLICT',
      message: '選択した時間帯はすでに予約されています。',
      conflicts: [{ reservation_id: 9, start_time: '09:30', end_time: '10:30' }],
    },
  });
  await assert.rejects(
    () => api.post('/api/reservations', {}),
    (err) => {
      assert.equal(err.status, 409);
      assert.equal(err.extra.conflicts[0].reservation_id, 9);
      return true;
    }
  );
});

test('500: INTERNAL_ERROR として扱う(本文が無い場合も含む)', async () => {
  stubFetch(500, undefined);
  await assert.rejects(
    () => api.get('/api/me'),
    (err) => err.status === 500 && err.code === 'INTERNAL_ERROR'
  );
});
