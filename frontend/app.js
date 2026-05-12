const state = {
  meta: { building_types: [], facility_types: [], query_categories: [] },
  campuses: [],
  buildings: [],
  facilities: [],
  queryMode: "traditional",
  traditionalEntity: "campuses",
  browseTab: "history",
  browseEntity: "campuses",
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
    ["campus_name", "校区"],
  ],
  courses: [
    ["offering_id", "开设ID"],
    ["course_name", "课程"],
    ["course_code", "课程代码"],
    ["teachers", "教师"],
    ["semester", "学期"],
    ["schedules", "排课"],
  ],
  activities: [
    ["activity_id", "ID"],
    ["name", "活动"],
    ["start_time", "开始时间"],
    ["organizer", "主办单位"],
    ["facility_name", "设施"],
    ["campus_name", "校区"],
    ["participant_count", "参与数"],
  ],
  queryLogs: [
    ["log_id", "ID"],
    ["query_time", "时间"],
    ["user_name", "用户"],
    ["query_category", "类别"],
    ["query_content", "内容"],
  ],
  popularQueries: [
    ["query_category", "类别"],
    ["query_count", "次数"],
    ["latest_query", "最近查询"],
    ["latest_query_time", "最近时间"],
  ],
  popularActivities: [
    ["activity_name", "活动"],
    ["participant_count", "参与数"],
    ["start_time", "开始时间"],
    ["organizer", "主办单位"],
    ["facility_name", "设施"],
    ["campus_name", "校区"],
  ],
};

const editableEntities = new Set(["buildings", "facilities", "activities"]);

const traditionalDefinitions = {
  campuses: {
    endpoint: "/api/campuses",
    fields: [{ name: "q", label: "关键词", type: "search", placeholder: "校区名或地址" }],
  },
  buildings: {
    endpoint: "/api/buildings",
    fields: [
      { name: "q", label: "关键词", type: "search", placeholder: "建筑名、类型或校区" },
      { name: "campus_id", label: "所属校区", type: "select", source: "campuses", placeholder: "全部校区" },
      { name: "type", label: "建筑类型", type: "select", source: "buildingTypes", placeholder: "全部类型" },
    ],
  },
  facilities: {
    endpoint: "/api/facilities",
    fields: [
      { name: "q", label: "关键词", type: "search", placeholder: "设施名、类型或建筑" },
      { name: "campus_id", label: "所在校区", type: "select", source: "campuses", placeholder: "全部校区" },
      { name: "building_id", label: "所属建筑", type: "select", source: "buildings", placeholder: "全部建筑" },
      { name: "type", label: "设施类型", type: "select", source: "facilityTypes", placeholder: "全部类型" },
    ],
  },
  courses: {
    endpoint: "/api/courses",
    fields: [
      { name: "q", label: "关键词", type: "search", placeholder: "课程、代码或教师" },
      { name: "course_name", label: "课程名称", type: "text", placeholder: "例如：数据库系统原理" },
      { name: "course_code", label: "课程代码", type: "text", placeholder: "例如：COMP130015" },
      { name: "teacher", label: "教师", type: "text", placeholder: "例如：李芳" },
      { name: "semester", label: "学期", type: "text", placeholder: "例如：2025-2026 春季学期" },
      {
        name: "day_of_week",
        label: "星期",
        type: "select",
        options: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        placeholder: "全部",
      },
    ],
  },
  activities: {
    endpoint: "/api/activities",
    fields: [
      { name: "q", label: "关键词", type: "search", placeholder: "活动、简介、主办方或地点" },
      { name: "organizer", label: "主办单位", type: "text", placeholder: "例如：计算机科学技术学院" },
      { name: "campus_id", label: "所在校区", type: "select", source: "campuses", placeholder: "全部校区" },
      { name: "facility_id", label: "举办设施", type: "select", source: "facilities", placeholder: "全部设施" },
      { name: "start_from", label: "开始不早于", type: "datetime-local" },
      { name: "start_to", label: "开始不晚于", type: "datetime-local" },
    ],
  },
};

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

function formPayload(form) {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectOptions(source) {
  if (source === "campuses") {
    return state.campuses.map((row) => [row.campus_id, row.name]);
  }
  if (source === "buildings") {
    return state.buildings.map((row) => [row.building_id, row.name]);
  }
  if (source === "facilities") {
    return state.facilities.map((row) => [row.facility_id, row.name]);
  }
  if (source === "buildingTypes") {
    return state.meta.building_types.map((value) => [value, value]);
  }
  if (source === "facilityTypes") {
    return state.meta.facility_types.map((value) => [value, value]);
  }
  if (source === "queryCategories") {
    return state.meta.query_categories.map((value) => [value, value]);
  }
  return [];
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
    health.textContent = db.connected ? `后端正常 · ${db.mode}` : "后端正常 · 数据库未连接";
    health.title = db.connected ? "" : db.error || "";
  } catch (error) {
    health.className = "status warn";
    health.textContent = "后端未连接";
    health.title = error.message;
  }
}

function renderInputField(field) {
  const id = `traditional-${field.name}`;
  if (field.type === "select") {
    const options = field.options ? field.options.map((value) => [value, value]) : selectOptions(field.source);
    const optionHtml = [
      field.placeholder ? `<option value="">${escapeHtml(field.placeholder)}</option>` : "",
      ...options.map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`),
    ].join("");
    return `<label for="${id}">${escapeHtml(field.label)}<select id="${id}" name="${escapeHtml(field.name)}">${optionHtml}</select></label>`;
  }
  return `
    <label for="${id}">
      ${escapeHtml(field.label)}
      <input id="${id}" name="${escapeHtml(field.name)}" type="${escapeHtml(field.type)}" placeholder="${escapeHtml(field.placeholder || "")}" />
    </label>
  `;
}

function renderTraditionalFields() {
  const entity = $("#traditionalEntity").value;
  state.traditionalEntity = entity;
  const definition = traditionalDefinitions[entity];
  $("#traditionalFields").innerHTML = definition.fields.map(renderInputField).join("");
}

function setQueryMode(mode) {
  state.queryMode = mode;
  $$(".mode-button").forEach((button) => button.classList.toggle("is-active", button.dataset.queryMode === mode));
  $("#traditionalPane").classList.toggle("hidden", mode !== "traditional");
  $("#naturalPane").classList.toggle("hidden", mode !== "natural");
}

async function runTraditionalQuery(event) {
  if (event) {
    event.preventDefault();
  }
  const form = $("#traditionalQueryForm");
  const payload = formPayload(form);
  const entity = payload.entity;
  delete payload.entity;
  const definition = traditionalDefinitions[entity];
  const result = await api(`${definition.endpoint}${buildQuery(payload)}`);
  renderTable($("#queryResult"), entity, result.items || [], { editable: editableEntities.has(entity), framed: true });
  showMessage(`传统查询完成，返回 ${(result.items || []).length} 条结果`);
}

async function askNaturalLanguage(event) {
  if (event) {
    event.preventDefault();
  }
  const payload = formPayload($("#nlQueryForm"));
  const result = await api("/api/nl-query", { method: "POST", body: JSON.stringify(payload) });
  renderNaturalLanguageAnswer(result);
  if (state.browseTab === "history" || state.browseTab === "popularQueries") {
    await loadBrowse();
  }
  showMessage(`自然语言查询完成，返回 ${result.row_count} 条结果`);
}

function renderNaturalLanguageAnswer(result) {
  const params = result.params && result.params.length ? JSON.stringify(result.params, null, 2) : "[]";
  $("#queryResult").innerHTML = `
    <div class="answer-box">
      <div class="answer-summary">
        <div><strong>识别意图</strong><br />${escapeHtml(result.title)}</div>
        <div><strong>回答摘要</strong><br />${escapeHtml(result.answer)}</div>
        <div><strong>类别</strong><br />${escapeHtml(result.category)}</div>
        <div><strong>参数</strong><br />${escapeHtml(params)}</div>
      </div>
      <pre>${escapeHtml(result.sql)}</pre>
      <div class="sql-result">${renderRows(result.rows || [])}</div>
    </div>
  `;
}

function renderTable(target, entity, rows, options = {}) {
  if (!rows.length) {
    target.innerHTML = `<div class="empty">没有匹配数据</div>`;
    return;
  }
  const columns = entityColumns[entity];
  const canEdit = options.editable && editableEntities.has(entity);
  const header = columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("");
  const editHeader = canEdit ? "<th>操作</th>" : "";
  const body = rows
    .map((row) => {
      const cells = columns.map(([key]) => `<td>${escapeHtml(row[key] ?? "")}</td>`).join("");
      const actions = canEdit
        ? `<td><div class="row-actions"><button type="button" data-edit-entity="${entity}" data-edit='${escapeHtml(JSON.stringify(row))}'>编辑</button></div></td>`
        : "";
      return `<tr>${cells}${actions}</tr>`;
    })
    .join("");
  const table = `<table><thead><tr>${header}${editHeader}</tr></thead><tbody>${body}</tbody></table>`;
  target.innerHTML = options.framed ? `<div class="table-wrap">${table}</div>` : table;
  $$("[data-edit]").forEach((button) => {
    button.addEventListener("click", () => fillEditForm(button.dataset.editEntity, JSON.parse(button.dataset.edit)));
  });
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

function browseFilterField(field) {
  if (field.type === "select") {
    const options = selectOptions(field.source);
    return `
      <label>
        ${escapeHtml(field.label)}
        <select name="${escapeHtml(field.name)}">
          <option value="">${escapeHtml(field.placeholder || "全部")}</option>
          ${options.map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join("")}
        </select>
      </label>
    `;
  }
  return `
    <label>
      ${escapeHtml(field.label)}
      <input name="${escapeHtml(field.name)}" type="${escapeHtml(field.type)}" value="${escapeHtml(field.value || "")}" placeholder="${escapeHtml(field.placeholder || "")}" />
    </label>
  `;
}

function renderBrowseFilters() {
  const form = $("#browseFilterForm");
  if (state.browseTab === "history") {
    form.classList.remove("compact-only");
    form.innerHTML = [
      browseFilterField({ name: "q", label: "关键词", type: "search", placeholder: "内容、类别或用户" }),
      browseFilterField({ name: "query_category", label: "类别", type: "select", source: "queryCategories", placeholder: "全部类别" }),
      browseFilterField({ name: "user_id", label: "用户 ID", type: "number" }),
      browseFilterField({ name: "limit", label: "数量", type: "number", value: "20" }),
      `<div class="actions"><button type="submit">浏览</button></div>`,
    ].join("");
    return;
  }
  if (state.browseTab === "popularQueries" || state.browseTab === "popularActivities") {
    form.classList.add("compact-only");
    form.innerHTML = [
      browseFilterField({ name: "limit", label: "数量", type: "number", value: "10" }),
      `<div class="actions"><button type="submit">浏览</button></div>`,
    ].join("");
    return;
  }
  if (state.browseTab === "data") {
    form.classList.remove("compact-only");
    form.innerHTML = `
      <label>
        数据对象
        <select name="entity" id="browseEntity">
          <option value="campuses">校区</option>
          <option value="buildings">建筑</option>
          <option value="facilities">设施</option>
          <option value="courses">课程</option>
          <option value="activities">活动</option>
        </select>
      </label>
      ${browseFilterField({ name: "q", label: "关键词", type: "search" })}
      <div class="actions"><button type="submit">浏览</button></div>
    `;
    $("#browseEntity").value = state.browseEntity;
    return;
  }
  form.classList.add("compact-only");
  form.innerHTML = `<div class="actions"><button type="submit">执行</button></div>`;
}

async function loadBrowse(event) {
  if (event) {
    event.preventDefault();
  }
  const form = $("#browseFilterForm");
  const params = formPayload(form);
  const target = $("#browseContent");

  if (state.browseTab === "history") {
    const payload = await api(`/api/query-logs${buildQuery(params)}`);
    renderTable(target, "queryLogs", payload.items || []);
    return;
  }
  if (state.browseTab === "popularQueries") {
    const payload = await api(`/api/insights/popular-queries${buildQuery(params)}`);
    renderTable(target, "popularQueries", payload.items || []);
    return;
  }
  if (state.browseTab === "popularActivities") {
    const payload = await api(`/api/insights/popular-activities${buildQuery(params)}`);
    renderTable(target, "popularActivities", payload.items || []);
    return;
  }
  if (state.browseTab === "data") {
    const entity = params.entity || state.browseEntity;
    state.browseEntity = entity;
    delete params.entity;
    const payload = await api(`/api/${entity}${buildQuery(params)}`);
    renderTable(target, entity, payload.items || [], { editable: editableEntities.has(entity) });
    return;
  }
  await loadSqlExamples(target);
}

async function loadSqlExamples(target = $("#browseContent")) {
  const payload = await api("/api/sql-examples");
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

function setBrowseTab(tab) {
  state.browseTab = tab;
  $$(".browse-tabs .tab").forEach((button) => button.classList.toggle("is-active", button.dataset.browse === tab));
  renderBrowseFilters();
}

function showForm(formId) {
  $$(".maintenance-tabs .tab").forEach((tab) => tab.classList.toggle("is-active", tab.dataset.form === formId));
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
  if (state.browseTab === "history" || state.browseTab === "popularQueries") {
    await loadBrowse();
  }
}

async function reloadAfterWrite(entity) {
  await loadReferenceData();
  $("#traditionalEntity").value = entity;
  renderTraditionalFields();
  await runTraditionalQuery();
  if (state.browseTab === "data") {
    state.browseEntity = entity;
    renderBrowseFilters();
    await loadBrowse();
  }
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

function bindEvents() {
  $$(".mode-button").forEach((button) => {
    button.addEventListener("click", () => setQueryMode(button.dataset.queryMode));
  });
  $("#traditionalEntity").addEventListener("change", () => {
    renderTraditionalFields();
    runTraditionalQuery().catch((error) => showMessage(error.message, true));
  });
  $("#traditionalQueryForm").addEventListener("submit", (event) => runTraditionalQuery(event).catch((error) => showMessage(error.message, true)));
  $("#clearTraditionalBtn").addEventListener("click", () => {
    $("#traditionalQueryForm").reset();
    renderTraditionalFields();
    runTraditionalQuery().catch((error) => showMessage(error.message, true));
  });
  $("#nlQueryForm").addEventListener("submit", (event) => askNaturalLanguage(event).catch((error) => showMessage(error.message, true)));
  $$("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#nlQuestion").value = button.dataset.question;
      askNaturalLanguage().catch((error) => showMessage(error.message, true));
    });
  });
  $$(".browse-tabs .tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      setBrowseTab(tab.dataset.browse);
      loadBrowse().catch((error) => showMessage(error.message, true));
    });
  });
  $("#refreshBrowseBtn").addEventListener("click", () => loadBrowse().catch((error) => showMessage(error.message, true)));
  $("#browseFilterForm").addEventListener("submit", (event) => loadBrowse(event).catch((error) => showMessage(error.message, true)));
  $("#browseFilterForm").addEventListener("change", (event) => {
    if (event.target.name === "entity") {
      loadBrowse().catch((error) => showMessage(error.message, true));
    }
  });
  $$(".maintenance-tabs .tab").forEach((tab) => tab.addEventListener("click", () => showForm(tab.dataset.form)));
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
  renderTraditionalFields();
  renderBrowseFilters();
  await runTraditionalQuery();
  await loadBrowse();
}

init().catch((error) => showMessage(error.message, true));
