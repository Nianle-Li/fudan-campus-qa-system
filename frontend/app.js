const state = {
  meta: { building_types: [], facility_types: [], query_categories: [] },
  campuses: [],
  buildings: [],
  facilities: [],
  activeEntity: "campuses",
};

const entityColumns = {
  campuses: [
    ["campus_id", "ID"],
    ["name", "校区"],
    ["address", "地址"],
  ],
  buildings: [
    ["building_id", "ID"],
    ["name", "建筑"],
    ["type", "类型"],
    ["campus_name", "校区"],
  ],
  facilities: [
    ["facility_id", "ID"],
    ["name", "设施"],
    ["type", "类型"],
    ["open_time", "开放时间"],
    ["building_name", "建筑"],
  ],
  courses: [
    ["offering_id", "开设ID"],
    ["course_name", "课程"],
    ["course_code", "课程代码"],
    ["teachers", "教师"],
    ["schedules", "排课"],
  ],
  activities: [
    ["activity_id", "ID"],
    ["name", "活动"],
    ["start_time", "开始时间"],
    ["organizer", "主办单位"],
    ["facility_name", "设施"],
    ["participant_count", "参与数"],
  ],
};

const editableEntities = new Set(["buildings", "facilities", "activities"]);

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `请求失败：${response.status}`);
  }
  return payload;
}

function showMessage(text, isError = false) {
  const box = $("#message");
  box.textContent = text;
  box.classList.toggle("error", isError);
}

function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      query.set(key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

function fillSelect(select, rows, valueKey, labelKey, placeholder) {
  select.innerHTML = "";
  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.appendChild(option);
  }
  rows.forEach((row) => {
    const option = document.createElement("option");
    option.value = row[valueKey];
    option.textContent = row[labelKey];
    select.appendChild(option);
  });
}

function fillTypeSelect(select, values) {
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function refreshOptions() {
  $$("[data-options='buildingTypes']").forEach((select) => fillTypeSelect(select, state.meta.building_types));
  $$("[data-options='facilityTypes']").forEach((select) => fillTypeSelect(select, state.meta.facility_types));
  $$("[data-options='queryCategories']").forEach((select) => fillTypeSelect(select, state.meta.query_categories));
  $$("[data-options='campuses']").forEach((select) => fillSelect(select, state.campuses, "campus_id", "name"));
  $$("[data-options='buildings']").forEach((select) => fillSelect(select, state.buildings, "building_id", "name"));
  $$("[data-options='facilities']").forEach((select) => fillSelect(select, state.facilities, "facility_id", "name"));
}

async function loadReferenceData() {
  const [meta, campuses, buildings, facilities] = await Promise.all([
    api("/api/meta"),
    api("/api/campuses"),
    api("/api/buildings"),
    api("/api/facilities"),
  ]);
  state.meta = meta;
  state.campuses = campuses.items;
  state.buildings = buildings.items;
  state.facilities = facilities.items;
  refreshOptions();
}

async function checkHealth() {
  const health = $("#health");
  try {
    const payload = await api("/api/health");
    const db = payload.database;
    health.className = `status ${db.connected ? "ok" : "warn"}`;
    health.textContent = db.connected ? `后端正常 · ${db.mode}` : `后端正常 · 数据库未连接`;
    if (!db.connected && db.error) {
      health.title = db.error;
    }
  } catch (error) {
    health.className = "status warn";
    health.textContent = "后端未连接";
    health.title = error.message;
  }
}

async function loadEntity() {
  const entity = $("#entitySelect").value;
  state.activeEntity = entity;
  const q = $("#searchInput").value.trim();
  const payload = await api(`/api/${entity}${buildQuery({ q })}`);
  renderTable(entity, payload.items || []);
}

function renderTable(entity, rows) {
  const target = $("#dataTable");
  if (!rows.length) {
    target.innerHTML = `<div class="empty">没有匹配数据</div>`;
    return;
  }
  const columns = entityColumns[entity];
  const canEdit = editableEntities.has(entity);
  const header = columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("");
  const editHeader = canEdit ? "<th>操作</th>" : "";
  const body = rows
    .map((row) => {
      const cells = columns.map(([key]) => `<td>${escapeHtml(row[key] ?? "")}</td>`).join("");
      const actions = canEdit
        ? `<td><div class="row-actions"><button type="button" data-edit='${escapeHtml(JSON.stringify(row))}'>编辑</button></div></td>`
        : "";
      return `<tr>${cells}${actions}</tr>`;
    })
    .join("");
  target.innerHTML = `<table><thead><tr>${header}${editHeader}</tr></thead><tbody>${body}</tbody></table>`;
  $$("[data-edit]").forEach((button) => {
    button.addEventListener("click", () => fillEditForm(entity, JSON.parse(button.dataset.edit)));
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showForm(formId) {
  $$(".tab").forEach((tab) => tab.classList.toggle("is-active", tab.dataset.form === formId));
  $$(".crud-form").forEach((form) => form.classList.toggle("hidden", form.id !== formId));
}

function setFormValues(form, values) {
  Object.entries(values).forEach(([key, value]) => {
    const field = form.elements[key];
    if (!field) return;
    if (field.type === "datetime-local" && value) {
      field.value = String(value).slice(0, 16).replace(" ", "T");
    } else {
      field.value = value ?? "";
    }
  });
}

function fillEditForm(entity, row) {
  if (entity === "buildings") {
    showForm("buildingForm");
    setFormValues($("#buildingForm"), row);
  } else if (entity === "facilities") {
    showForm("facilityForm");
    setFormValues($("#facilityForm"), row);
  } else if (entity === "activities") {
    showForm("activityForm");
    setFormValues($("#activityForm"), row);
  }
  showMessage("已载入记录，可修改后保存");
}

function formPayload(form) {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

async function saveBuilding(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = formPayload(form);
  const id = payload.building_id;
  delete payload.building_id;
  await api(id ? `/api/buildings/${id}` : "/api/buildings", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(payload),
  });
  showMessage(id ? "建筑已更新" : "建筑已新增");
  form.reset();
  await reloadAfterWrite("buildings");
}

async function saveFacility(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = formPayload(form);
  const id = payload.facility_id;
  delete payload.facility_id;
  await api(id ? `/api/facilities/${id}` : "/api/facilities", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(payload),
  });
  showMessage(id ? "设施已更新" : "设施已新增");
  form.reset();
  await reloadAfterWrite("facilities");
}

async function saveActivity(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = formPayload(form);
  const id = payload.activity_id;
  delete payload.activity_id;
  await api(id ? `/api/activities/${id}` : "/api/activities", {
    method: id ? "PUT" : "POST",
    body: JSON.stringify(payload),
  });
  showMessage(id ? "活动已更新" : "活动已新增");
  form.reset();
  await reloadAfterWrite("activities");
}

async function saveQueryLog(event) {
  event.preventDefault();
  const payload = formPayload(event.currentTarget);
  const result = await api("/api/query-log", { method: "POST", body: JSON.stringify(payload) });
  showMessage(`查询记录已写入，log_id=${result.item.log_id}`);
  event.currentTarget.reset();
}

async function reloadAfterWrite(entity) {
  await loadReferenceData();
  $("#entitySelect").value = entity;
  await loadEntity();
}

async function deleteCurrent(kind) {
  const formMap = {
    building: ["buildingForm", "building_id", "/api/buildings/", "buildings"],
    facility: ["facilityForm", "facility_id", "/api/facilities/", "facilities"],
    activity: ["activityForm", "activity_id", "/api/activities/", "activities"],
  };
  const [formId, idKey, endpoint, entity] = formMap[kind];
  const form = $(`#${formId}`);
  const id = form.elements[idKey].value;
  if (!id) {
    showMessage("请先从表格中选择一条记录", true);
    return;
  }
  await api(`${endpoint}${id}`, { method: "DELETE" });
  showMessage("记录已删除");
  form.reset();
  await reloadAfterWrite(entity);
}

async function loadSqlExamples() {
  const payload = await api("/api/sql-examples");
  const target = $("#sqlExamples");
  target.innerHTML = payload.items
    .map((item) => {
      const rows = item.rows || [];
      return `
        <article class="sql-item">
          <div class="sql-heading">${escapeHtml(item.title)}</div>
          <pre>${escapeHtml(item.sql)}</pre>
          <div class="sql-result">${renderRows(rows)}</div>
        </article>
      `;
    })
    .join("");
}

function renderRows(rows) {
  if (!rows.length) {
    return `<div class="empty">查询无结果</div>`;
  }
  const keys = Object.keys(rows[0]);
  const header = keys.map((key) => `<th>${escapeHtml(key)}</th>`).join("");
  const body = rows
    .map((row) => `<tr>${keys.map((key) => `<td>${escapeHtml(row[key] ?? "")}</td>`).join("")}</tr>`)
    .join("");
  return `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

function bindEvents() {
  $("#refreshBtn").addEventListener("click", () => loadEntity().catch((error) => showMessage(error.message, true)));
  $("#loadSqlBtn").addEventListener("click", () => loadSqlExamples().catch((error) => showMessage(error.message, true)));
  $("#entitySelect").addEventListener("change", () => loadEntity().catch((error) => showMessage(error.message, true)));
  $("#searchInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      loadEntity().catch((error) => showMessage(error.message, true));
    }
  });
  $$(".tab").forEach((tab) => tab.addEventListener("click", () => showForm(tab.dataset.form)));
  $$("[data-reset]").forEach((button) => {
    button.addEventListener("click", () => {
      $(`#${button.dataset.reset}`).reset();
      showMessage("表单已清空");
    });
  });
  $$("[data-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteCurrent(button.dataset.delete).catch((error) => showMessage(error.message, true)));
  });
  $("#buildingForm").addEventListener("submit", (event) => saveBuilding(event).catch((error) => showMessage(error.message, true)));
  $("#facilityForm").addEventListener("submit", (event) => saveFacility(event).catch((error) => showMessage(error.message, true)));
  $("#activityForm").addEventListener("submit", (event) => saveActivity(event).catch((error) => showMessage(error.message, true)));
  $("#queryLogForm").addEventListener("submit", (event) => saveQueryLog(event).catch((error) => showMessage(error.message, true)));
}

async function init() {
  bindEvents();
  await checkHealth();
  await loadReferenceData();
  await loadEntity();
  await loadSqlExamples();
}

init().catch((error) => showMessage(error.message, true));
