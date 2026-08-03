// S06 会議室管理画面 (docs/P002-frontend-spec.md §3 S06, §4.4〜§4.7)
//
// ★deviation★ loginPage.jsと同様、DOM非依存のコントローラ(unit test対象)と
// 実際のDOM描画(mountRoomManagementPage、手動/結合確認のみ)を分離している。

export function validateRoomInput(name, capacity) {
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
  return null;
}

/**
 * 会議室管理画面のコントローラ。DOMに依存しない。
 * @param {{list: Function, create: Function, update: Function, remove: Function}} roomApi
 */
export function createRoomManagementController(roomApi) {
  const state = { rooms: [], error: null };

  return {
    getState() {
      return state;
    },
    async loadRooms() {
      state.rooms = await roomApi.list(true);
      return state.rooms;
    },
    async submitCreate(name, capacity, equipment = [], isActive = true) {
      const validationError = validateRoomInput(name, capacity);
      if (validationError) {
        state.error = validationError;
        return { ok: false, message: validationError };
      }
      try {
        await roomApi.create({ name, capacity: Number(capacity), equipment, is_active: isActive });
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
  };
}

export function mountRoomManagementPage(container, roomApi) {
  const controller = createRoomManagementController(roomApi);

  async function render() {
    const state = controller.getState();
    container.innerHTML = `
      <h2>会議室管理</h2>
      <table>
        <thead><tr><th>名前</th><th>収容人数</th><th>状態</th><th></th></tr></thead>
        <tbody>
          ${state.rooms.map((r) => `
            <tr>
              <td>${r.name}</td><td>${r.capacity}</td><td>${r.is_active ? "有効" : "無効"}</td>
              <td><button data-deactivate="${r.id}" ${r.is_active ? "" : "disabled"}>無効化</button></td>
            </tr>`).join("")}
        </tbody>
      </table>
      <form id="room-create-form">
        <div class="form-row"><label>会議室名</label><input name="name" /></div>
        <div class="form-row"><label>収容人数</label><input name="capacity" type="number" /></div>
        <button type="submit">登録</button>
        <div class="error-message">${state.error || ""}</div>
      </form>
    `;
    container.querySelector("#room-create-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      await controller.submitCreate(form.name.value, form.capacity.value);
      render();
    });
    container.querySelectorAll("[data-deactivate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await controller.submitDeactivate(Number(btn.dataset.deactivate));
        render();
      });
    });
  }

  controller.loadRooms().then(render);
  return controller;
}
