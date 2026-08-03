// S06 会議室管理画面 (docs/P002-frontend-spec.md §3 S06, §4.4〜§4.7)
//
// ★deviation★ loginPage.jsと同様、DOM非依存のコントローラ(unit test対象)と
// 実際のDOM描画(mountRoomManagementPage、手動/結合確認のみ)を分離している。

export function validateRoomInput(name, capacity, description = "") {
  if (!name || !name.trim()) {
    return "会議室名を入力してください";
  }
  if (name.length > 50) {
    return "会議室名は50文字以内で入力してください";
  }
  const capacityNum = Number(capacity);
  if (!Number.isInteger(capacityNum) || capacityNum < 1) {
    return "収容人数は1以上の整数で入力してください";
  }
  // ★CR-002で追加: 説明文は任意入力・最大200文字(docs/P002-frontend-spec.md §3 S06)。
  if (description && description.length > 200) {
    return "説明文は200文字以内で入力してください";
  }
  return null;
}

/**
 * 会議室管理画面のコントローラ。DOMに依存しない。
 * @param {{list: Function, create: Function, update: Function, remove: Function}} roomApi
 */
export function createRoomManagementController(roomApi) {
  // ★CR-002で追加: state.editingRoomId は現在編集中の会議室id(未編集時はnull)。
  const state = { rooms: [], error: null, editingRoomId: null };

  return {
    getState() {
      return state;
    },
    async loadRooms() {
      state.rooms = await roomApi.list(true);
      return state.rooms;
    },
    async submitCreate(name, capacity, equipment = [], isActive = true, description = "") {
      const validationError = validateRoomInput(name, capacity, description);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        await roomApi.create({
          name, capacity: Number(capacity), equipment, is_active: isActive,
          description: description || null,
        });
        state.error = null;
        await this.loadRooms();
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
    async submitDeactivate(roomId) {
      try {
        await roomApi.remove(roomId);
        state.error = null;
        await this.loadRooms();
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
    // ★CR-002で追加: 編集フォームの開始/中断/送信。
    startEdit(roomId) {
      state.editingRoomId = roomId;
    },
    cancelEdit() {
      state.editingRoomId = null;
    },
    async submitUpdate(roomId, name, capacity, equipment = [], isActive = true, description = "") {
      const validationError = validateRoomInput(name, capacity, description);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        await roomApi.update(roomId, {
          name, capacity: Number(capacity), equipment, is_active: isActive,
          description: description || null,
        });
        state.error = null;
        state.editingRoomId = null;
        await this.loadRooms();
        return { ok: true };
      } catch (err) {
        state.error = err.message;
        return { ok: false, message: err.message };
      }
    },
  };
}

export function mountRoomManagementPage(container, roomApi) {
  const controller = createRoomManagementController(roomApi);

  async function render() {
    const state = controller.getState();
    const editing = state.rooms.find((r) => r.id === state.editingRoomId) || null;
    container.innerHTML = `
      <h2>会議室管理</h2>
      <table>
        <thead><tr><th>名前</th><th>収容人数</th><th>説明文</th><th>状態</th><th></th></tr></thead>
        <tbody>
          ${state.rooms.map((r) => `
            <tr>
              <td>${r.name}</td><td>${r.capacity}</td><td>${r.description || ""}</td>
              <td>${r.is_active ? "有効" : "無効"}</td>
              <td>
                <button data-edit="${r.id}">編集</button>
                <button data-deactivate="${r.id}" ${r.is_active ? "" : "disabled"}>無効化</button>
              </td>
            </tr>`).join("")}
        </tbody>
      </table>
      <form id="room-create-form">
        <h3>新規登録</h3>
        <div class="form-row"><label>会議室名</label><input name="name" /></div>
        <div class="form-row"><label>収容人数</label><input name="capacity" type="number" /></div>
        <div class="form-row"><label>説明文</label><textarea name="description" maxlength="200"></textarea></div>
        <button type="submit">登録</button>
        <div class="error-message">${state.error || ""}</div>
      </form>
      ${editing ? `
      <form id="room-edit-form">
        <h3>編集(${editing.name})</h3>
        <div class="form-row"><label>会議室名</label><input name="name" value="${editing.name}" /></div>
        <div class="form-row"><label>収容人数</label><input name="capacity" type="number" value="${editing.capacity}" /></div>
        <div class="form-row"><label>説明文</label><textarea name="description" maxlength="200">${editing.description || ""}</textarea></div>
        <button type="submit">更新</button>
        <button type="button" id="room-edit-cancel">キャンセル</button>
        <div class="error-message">${state.error || ""}</div>
      </form>` : ""}
    `;
    container.querySelector("#room-create-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      await controller.submitCreate(form.name.value, form.capacity.value, [], true, form.description.value);
      render();
    });
    container.querySelectorAll("[data-deactivate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await controller.submitDeactivate(Number(btn.dataset.deactivate));
        render();
      });
    });
    container.querySelectorAll("[data-edit]").forEach((btn) => {
      btn.addEventListener("click", () => {
        controller.startEdit(Number(btn.dataset.edit));
        render();
      });
    });
    const editForm = container.querySelector("#room-edit-form");
    if (editForm) {
      editForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;
        await controller.submitUpdate(
          editing.id, form.name.value, form.capacity.value, editing.equipment || [],
          editing.is_active, form.description.value,
        );
        render();
      });
      container.querySelector("#room-edit-cancel").addEventListener("click", () => {
        controller.cancelEdit();
        render();
      });
    }
  }

  controller.loadRooms().then(render);
  return controller;
}
