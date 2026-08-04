-- 0002_add_room_description.sql
-- CR-002: 会議室管理画面(S06)に説明文(description)を追加する (docs/P003-backend-spec.md §6.3 参照)
-- 既存行は description = NULL (未設定) として扱う。任意入力・最大200文字はアプリケーション層(validators.py)で検証する。

ALTER TABLE ROOMS ADD COLUMN description TEXT;
