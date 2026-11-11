import json
import sys
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

                                                              
try:
    from analytics import (
        analyze_station,
        build_recovery_plan,
        find_purchase_for_requirement,
        load_config,
        search_equipment,
    )
    from repository import get_all_equipment
except Exception:
    print("=" * 70)
    print("НЕ УДАЛОСЬ ИМПОРТИРОВАТЬ МОДУЛИ ПРОЕКТА")
    print("=" * 70)
    print("Убедитесь, что app.py лежит в одной папке с analytics.py,")
    print("repository.py, models.py и HackatonDB.db, и что вы запускаете")
    print("из этой папки:  cd путь\\к\\папке && python app.py")
    print("-" * 70)
    traceback.print_exc()
    print("=" * 70)
    sys.exit(1)


HTML = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Северный код</title>
<style>
  body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:#f5f7fa;
       color:#1f2937;margin:0;line-height:1.5}
  header{background:linear-gradient(135deg,#1e3a8a,#2563eb);color:#fff;padding:20px 28px}
  header h1{margin:0;font-size:20px}
  header .cfg{font-size:13px;opacity:.9;margin-top:4px}
  main{max-width:1100px;margin:0 auto;padding:20px}
  section{background:#fff;border-radius:10px;padding:18px 22px;margin-bottom:16px;
          box-shadow:0 1px 3px rgba(0,0,0,.06)}
  section h2{margin:0 0 12px;font-size:16px;padding-bottom:6px;
             border-bottom:2px solid #2563eb;display:inline-block}
  form{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
       gap:10px;align-items:end;margin:10px 0}
  label{display:block;font-size:12px;color:#6b7280;margin-bottom:4px}
  input,select{width:100%;padding:8px 10px;border:1px solid #e5e7eb;border-radius:6px;
               font:inherit;background:#fff;box-sizing:border-box}
  button{background:#2563eb;color:#fff;border:0;border-radius:6px;padding:9px 18px;
         font:inherit;cursor:pointer;font-weight:500}
  button:hover{background:#1d4ed8}
  .res{margin-top:12px}
  .msg{padding:10px 14px;border-radius:6px;font-size:14px;margin:6px 0}
  .ok{background:#f0fdf4;color:#166534}
  .warn{background:#fffbeb;color:#92400e}
  .err{background:#fef2f2;color:#991b1b}
  table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}
  th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #e5e7eb}
  th{background:#f9fafb;font-size:11px;text-transform:uppercase;color:#6b7280}
  tr.best{background:#f0fdf4}
  .pill{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
  .pill.ok{background:#dcfce7;color:#166534}
  .pill.err{background:#fee2e2;color:#991b1b}
  .pill.warn{background:#fef3c7;color:#92400e}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:10px}
  .kpi{background:#f9fafb;border-radius:8px;padding:12px 14px;border-left:3px solid #2563eb}
  .kpi .l{font-size:11px;color:#6b7280;text-transform:uppercase}
  .kpi .v{font-size:18px;font-weight:600;margin-top:2px}
  .kpi.ok{border-color:#16a34a}.kpi.err{border-color:#dc2626}.kpi.warn{border-color:#d97706}
  details{margin-top:10px}summary{cursor:pointer;color:#2563eb;font-size:13px}
  .card{border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;margin-top:10px}
  .card h4{margin:0 0 6px;font-size:14px}
  ul.clean{list-style:none;padding:0;margin:0;font-size:13px}
  ul.clean li{padding:3px 0}
  code{background:#f3f4f6;padding:1px 5px;border-radius:3px;font-size:12px}

  
  .file-btn {
    display: inline-flex; align-items: center; gap: 8px;
    background: #eef2ff; color: #2563eb; border: 1px solid #c7d2fe;
    border-radius: 6px; padding: 8px 16px; font: inherit; font-weight: 500;
    cursor: pointer; transition: background .15s;
  }
  .file-btn:hover { background: #e0e7ff; }
  .file-btn svg { width: 16px; height: 16px; }
  .file-btn input[type=file] { display: none; }

  .json-loader {
    display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
    margin-top: 10px;
  }
  .file-name {
    font-size: 13px; color: #374151; padding: 6px 10px;
    background: #f9fafb; border: 1px dashed #d1d5db; border-radius: 6px;
    min-width: 200px;
  }
  .file-name.empty { color: #9ca3af; font-style: italic; }

  .btn-ghost {
    background: transparent; color: #6b7280; border: 1px solid #e5e7eb;
    padding: 8px 14px;
  }
  .btn-ghost:hover { background: #f9fafb; color: #374151; }


</style>
</head>
<body>
<header>
  <h1>Северный код — планировщик восстановления станции</h1>
  <div class="cfg" id="cfg">загрузка конфига...</div>
</header>
<main>
  <section>
    <h2>1. Поиск оборудования по характеристикам</h2>
    <form onsubmit="event.preventDefault();search()">
      <div><label>Тип</label><select id="s1t" class="tsel"></select></div>
      <div><label>Мин. производительность</label><input type="number" id="s1c" value="8"></div>
      <div><label>Темп. эксплуатации, °C</label><input type="number" id="s1p" value="-30"></div>
      <div><button>Найти</button></div>
    </form>
    <div class="res" id="r1"></div>
  </section>

  <section>
    <h2>2. Подбор закупки</h2>
    <form onsubmit="event.preventDefault();offers()">
      <div><label>Тип</label><select id="s2t" class="tsel"></select></div>
      <div><label>Мин. производительность</label><input type="number" id="s2c" value="8"></div>
      <div><label>Темп. эксплуатации, °C</label><input type="number" id="s2p" value="-30"></div>
      <div><label>Дедлайн, дней</label><input type="number" id="s2d" value="14"></div>
      <div><button>Подобрать</button></div>
    </form>
    <div class="res" id="r2"></div>
  </section>

  <section>
    <h2>3. Потребности станции</h2>
    <button onclick="station()" style="margin-top: 12px; margin-left:6px">
      Проанализировать
    </button>
    <div class="res" id="r3"></div>
</section>

  <section>
    <h2>4. План восстановления</h2>

    
    <form onsubmit="event.preventDefault();plan()" style="margin-top:12px">
      <div><label>Бюджет, ₽</label>
        <input type="number" id="s4b" placeholder="из конфига"></div>
      <div><label>Дедлайн, дней</label>
        <input type="number" id="s4d" placeholder="из конфига"></div>
      <div><button>Построить план</button></div>
    </form>

    
    <div style="margin-top:14px; padding:12px 14px; background:#f9fafb;
                border-radius:8px; border:1px solid #e5e7eb">
      <label style="display:block; font-size:12px; color:#6b7280;
                    text-transform:uppercase; letter-spacing:.03em; margin-bottom:8px">
        Или загрузить параметры из JSON
      </label>

      <div class="json-loader">
        
        <label class="file-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          Выбрать JSON
          <input type="file" id="s4file" accept=".json"
                onchange="loadJsonConfig(event)">
        </label>

        
        <span class="file-name empty" id="s4file-name">файл не выбран</span>

        
        <button type="button" class="btn-ghost" onclick="downloadConfig()"
                style="margin-left:auto">Скачать шаблон</button>
      </div>

      <div id="s4file-status" style="font-size:12px; margin-top:8px"></div>
    </div>

    <div class="res" id="r4"></div>
  </section>

</main>

<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>Number(n).toLocaleString('ru-RU')+' ₽';
const m=(t,k='ok')=>`<div class="msg ${k}">${esc(t)}</div>`;
const tbl=(h,rows,clsFn)=>`<table><thead><tr>${h.map(x=>`<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${
  rows.map((r,i)=>`<tr class="${clsFn?clsFn(r,i):''}">${r.map(c=>`<td>${c??''}</td>`).join('')}</tr>`).join('')
}</tbody></table>`;

async function api(url,body){
  const opt=body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{};
  const r=await fetch(url,opt);
  const d=await r.json();
  if(!r.ok) throw new Error(d.error||('HTTP '+r.status));
  return d;
}

async function loadCfg(){
  try{
    const c=await api('/api/config');
    $('cfg').textContent=`Бюджет: ${money(c.recommended_budget_rub)} · Срок: ${c.recovery_deadline_days} дней`;
  }catch(e){$('cfg').textContent='конфиг не загружен: '+e.message;}
}

async function loadTypes(){
  try{
    const ts=await api('/api/types');
    const opts=ts.map(t=>`<option>${esc(t.type)}</option>`).join('');
    document.querySelectorAll('.tsel').forEach(s=>s.innerHTML=opts);
  }catch(e){console.error(e);}
}

async function search(){
  const el=$('r1'); el.innerHTML=m('поиск...','warn');
  try{
    const d=await api('/api/search',{
      equipment_type:$('s1t').value,
      min_capacity:+$('s1c').value,
      operating_temperature_c:+$('s1p').value});
    if(!d.found){el.innerHTML=m(d.message||'не найдено','warn');return;}
    el.innerHTML=m('Найдено: '+d.count,'ok')+tbl(
      ['ID','Название','Производительность','Темп. мин.','Установка'],
      d.models.map(x=>[`<code>${esc(x.equipment_id)}</code>`,esc(x.model_name),
        `${x.capacity} ${esc(x.capacity_unit)}`,`${x.min_operating_temperature_c} °C`,
        `${x.installation_days} дн.`]));
  }catch(e){el.innerHTML=m(e.message,'err');}
}

async function offers(){
  const el=$('r2'); el.innerHTML=m('подбор...','warn');
  try{
    const d=await api('/api/offers',{
      equipment_type:$('s2t').value,
      min_capacity:+$('s2c').value,
      operating_temperature_c:+$('s2p').value,
      deadline_days:+$('s2d').value});
    let h='';
    if(!d.found) h+=m(d.message||'нет предложений','warn');
    else h+=m(`Лучший: ${d.best.supplier_name} — ${d.best.model_name} за ${money(d.best.total_cost_rub)} (готов ${d.best.ready_days} дн.)`,'ok');
    if(d.candidates?.length){
      h+='<h4>Подходящие</h4>'+tbl(
        ['Поставщик','Модель','Цена','Доставка','Итого','Готов','Остаток'],
        d.candidates.map(c=>[esc(c.supplier_name),`<code>${esc(c.equipment_id)}</code> ${esc(c.model_name)}`,
          money(c.unit_price_rub),money(c.delivery_cost_rub),`<b>${money(c.total_cost_rub)}</b>`,
          c.ready_days+' дн.',c.stock_quantity]),
        (_,i)=>i===0?'best':'');
    }
    if(d.excluded?.length){
      h+=`<details><summary>Исключённые (${d.excluded.length})</summary>`+tbl(
        ['Offer','Поставщик','Цена','Остаток','Причина'],
        d.excluded.map(x=>[`<code>${esc(x.offer_id)}</code>`,esc(x.supplier_name||x.supplier_id),
          money(x.unit_price_rub),x.stock_quantity,esc((x.reasons||[]).join('; '))]))+'</details>';
    }
    el.innerHTML=h;
  }catch(e){el.innerHTML=m(e.message,'err');}
}

async function station(){
  const el=$('r3'); el.innerHTML=m('анализ...','warn');
  try{
    const d=await api('/api/station');
    const s=d.stats;
    let h=`<div class="kpis">
      <div class="kpi"><div class="l">Объектов</div><div class="v">${s.total_objects}</div></div>
      <div class="kpi"><div class="l">Обязательных</div><div class="v">${s.mandatory_objects}</div></div>
      <div class="kpi ok"><div class="l">Обеспечено</div><div class="v">${s.fully_satisfied_objects}</div></div>
      <div class="kpi warn"><div class="l">Требуют замены</div><div class="v">${s.needs_replacement} потребн.</div></div>
    </div>`;
    for(const o of d.objects){
      const tag=o.mandatory?'<span class="pill err">обязательный</span>':'<span class="pill warn">опциональный</span>';
      const st=o.fully_satisfied?'<span class="pill ok">обеспечен</span>':'<span class="pill err">требует замены</span>';
      h+=`<div class="card"><h4>${esc(o.object_name)} <code>${esc(o.object_id)}</code> ${tag} ${st}</h4>`+
        tbl(['Станция','Тип','Требуется','Темп.','Срок','Установлено','Статус'],
          o.needs.map(n=>[`<code>${esc(n.station_id)}</code>`,esc(n.equipment_type),
            `${n.required_capacity} ${esc(n.capacity_unit)}`,`${n.operating_temperature_c} °C`,
            `${n.deadline_days} дн.`,esc(n.installed_equipment_id||'—'),
            n.status==='satisfied'?'<span class="pill ok">ок</span>':
              `<span class="pill err">${esc(n.reason)}</span>`]))+'</div>';
    }
    el.innerHTML=h;
  }catch(e){el.innerHTML=m(e.message,'err');}
}

function renderPlan(p){
  const c=p.cost;
  let h=`<div class="kpis">
    <div class="kpi"><div class="l">Закупки</div><div class="v">${money(c.unit_total_rub)}</div></div>
    <div class="kpi"><div class="l">Доставка</div><div class="v">${money(c.delivery_total_rub)}</div></div>
    <div class="kpi"><div class="l">Итого</div><div class="v">${money(c.total_rub)}</div></div>
    <div class="kpi ${c.overrun_rub>0?'err':'ok'}"><div class="l">${c.overrun_rub>0?'Превышение':'Остаток бюджета'}</div>
      <div class="v">${c.overrun_rub>0?money(c.overrun_rub):money(p.config.budget_rub-c.total_rub)}</div></div>
  </div>`;
  if(!p.success) h+='<div style="margin-top:12px">'+m('Не все обязательные объекты закрыты к сроку','err')+'</div>';
  h+=`<h4 style="margin-top:16px">Восстановленные (${p.restored_objects.length+p.restored_optional_objects.length})</h4><ul class="clean">`;
  for(const o of p.restored_objects) h+=`<li>✅ <b>${esc(o.object_name)}</b> <code>${esc(o.object_id)}</code>${o.already_satisfied?' (был обеспечен)':''}</li>`;
  for(const o of p.restored_optional_objects) h+=`<li>✅ <b>${esc(o.object_name)}</b> <code>${esc(o.object_id)}</code> — опциональный</li>`;
  h+='</ul>';
  if(p.failed_mandatory_objects?.length){
    h+='<h4 style="margin-top:16px">❌ Не удалось</h4><ul class="clean">';
    for(const o of p.failed_mandatory_objects) h+=`<li>❌ <b>${esc(o.object_name)}</b> — ${o.unmet_needs.length} потребн.</li>`;
    h+='</ul>';
  }
  if(p.unrestored_optional_objects?.length){
    h+=`<h4 style="margin-top:16px">Отложенные опциональные (${p.unrestored_optional_objects.length})</h4><ul class="clean">`;
    for(const o of p.unrestored_optional_objects) h+=`<li>⏸ ${esc(o.object_name)}</li>`;
    h+='</ul>';
  }
  if(p.purchases_by_supplier?.length){
    h+='<h4 style="margin-top:16px">Закупки по поставщикам</h4>';
    for(const sup of p.purchases_by_supplier){
      h+=`<div class="card"><h4>${esc(sup.supplier_name)} <code>${esc(sup.supplier_id)}</code>
        — доставка ${money(sup.delivery_cost_rub)}, ${sup.delivery_days} дн.</h4>`+
        tbl(['Модель','Тип','Цена','Для объекта','Готов'],
          sup.items.map(it=>[`<code>${esc(it.equipment_id)}</code> ${esc(it.model_name)}`,
            esc(it.equipment_type),money(it.unit_price_rub),esc(it.for_object_name),it.ready_days+' дн.']))+'</div>';
    }
  }
  return h;
}

async function plan(){
  const el=$('r4'); el.innerHTML=m('строим план...','warn');
  try{
    const p=new URLSearchParams();
    if($('s4b').value)p.set('budget',$('s4b').value);
    if($('s4d').value)p.set('deadline',$('s4d').value);
    const d=await api('/api/plan'+(p.toString()?'?'+p:''));
    el.innerHTML=renderPlan(d);
  }catch(e){el.innerHTML=m(e.message,'err');}
}

function loadJsonConfig(event){
  const file = event.target.files[0];
  const status = $('s4file-status');
  const nameEl = $('s4file-name');
  if (!file) return;

  nameEl.textContent = file.name;
  nameEl.classList.remove('empty');

  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      const budget   = data.recommended_budget_rub ?? data.budget   ?? null;
      const deadline = data.recovery_deadline_days ?? data.deadline ?? null;

      if (budget === null && deadline === null){
        status.innerHTML = m('В файле нет полей budget / recommended_budget_rub / deadline', 'warn');
        return;
      }
      if (budget !== null){
        if (!Number.isFinite(+budget) || +budget <= 0){
          status.innerHTML = m('budget должно быть положительным числом', 'err');
          return;
        }
        $('s4b').value = +budget;
      }
      if (deadline !== null){
        if (!Number.isFinite(+deadline) || +deadline <= 0){
          status.innerHTML = m('deadline должно быть положительным числом', 'err');
          return;
        }
        $('s4d').value = +deadline;
      }
      status.innerHTML = `<span style="color:#166534">✓ Загружено`
        + (budget   !== null ? ` · бюджет ${money(budget)}` : '')
        + (deadline !== null ? ` · дедлайн ${deadline} дн.` : '')
        + '</span>';
    } catch (err){
      status.innerHTML = m('Ошибка разбора JSON: ' + err.message, 'err');
    }
  };
  reader.onerror = () => status.innerHTML = m('Не удалось прочитать файл', 'err');
  reader.readAsText(file, 'utf-8');
}




loadCfg(); loadTypes();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, e, status=400):
        self._json({"error": str(e)}, status)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def log_message(self, *args):
        pass                             

                               
    def do_GET(self):
        p = urlparse(self.path)
        try:
            if p.path in ("/", "/index.html"):
                return self._html(HTML)

            if p.path == "/api/config":
                return self._json(load_config())

            if p.path == "/api/types":
                by = {}
                for e in get_all_equipment():
                    by.setdefault(e.equipment_type, set()).add(e.capacity_unit)
                return self._json(
                    [{"type": t, "units": sorted(u)} for t, u in sorted(by.items())]
                )

            if p.path == "/api/station":
                return self._json(analyze_station())

            if p.path == "/api/plan":
                q = parse_qs(p.query)
                b = int(q["budget"][0]) if "budget" in q else None
                d = int(q["deadline"][0]) if "deadline" in q else None
                return self._json(build_recovery_plan(b, d))


            self._json({"error": "not found"}, 404)
        except Exception as e:
            traceback.print_exc()
            self._err(e, 500)

                                
    def do_POST(self):
        p = urlparse(self.path)
        data = self._read_json()
        try:
            if p.path == "/api/search":
                return self._json(search_equipment(
                    data.get("equipment_type"),
                    int(data.get("min_capacity")),
                    int(data.get("operating_temperature_c")),
                ))

            if p.path == "/api/offers":
                return self._json(find_purchase_for_requirement(
                    data.get("equipment_type"),
                    int(data.get("min_capacity")),
                    int(data.get("operating_temperature_c")),
                    int(data.get("deadline_days")),
                    data.get("capacity_unit"),
                ))

            self._json({"error": "not found"}, 404)
        except (KeyError, TypeError, ValueError) as e:
            self._err(f"Некорректные параметры: {e}", 400)
        except Exception as e:
            traceback.print_exc()
            self._err(e, 500)


def main():
    host, port = "127.0.0.1", 8000
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as e:
        print(f"Не удалось занять {host}:{port} — {e}")
        print("Попробуйте другой порт: python app.py 8080")
        sys.exit(1)

    url = f"http://{host}:{port}"
    print("=" * 60)
    print(f"Сервер запущен: {url}")
    print("Откройте в браузере. Остановить: Ctrl+C")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен.")
        server.shutdown()


if __name__ == "__main__":
                                    
    if len(sys.argv) > 1:
        try:
            port_arg = int(sys.argv[1])
            _orig_main = main
            def main():              
                host = "127.0.0.1"
                server = ThreadingHTTPServer((host, port_arg), Handler)
                print(f"Сервер: http://{host}:{port_arg}")
                try:
                    webbrowser.open(f"http://{host}:{port_arg}")
                except Exception:
                    pass
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    server.shutdown()
        except ValueError:
            pass
    main()