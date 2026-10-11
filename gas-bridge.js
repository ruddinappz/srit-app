/* SRIT — jembatan Apps Script untuk hosting di GitHub Pages.
   Menggantikan google.script.run: setiap panggilan dikirim ke alamat /exec (doPost) lewat fetch.
   Seluruh kode aplikasi tetap memakai google.script.run seperti biasa (tanpa diubah). */
(function(){
  var KEY='srit_exec_url';
  function ls(op,k,v){try{return op==='g'?localStorage.getItem(k):(op==='s'?localStorage.setItem(k,v):localStorage.removeItem(k));}catch(e){return null;}}
  function valid(u){return /^https:\/\/script\.google\.com\/(a\/[^\/]+\/)?macros\/s\/[^\/]+\/exec$/.test(String(u||'').trim());}
  // 1) ?exec=ALAMAT di URL → simpan (berguna untuk membagikan tautan siap pakai)
  try{var q=new URLSearchParams(location.search).get('exec');if(q&&valid(q)){ls('s',KEY,q.trim());history.replaceState(null,'',location.pathname+location.hash);}}catch(e){}
  function execUrl(){var c=(window.SRIT_CONFIG&&window.SRIT_CONFIG.EXEC_URL)||'';return valid(c)?c.trim():(ls('g',KEY)||'');}
  window.SRIT_EXEC_URL=execUrl;

  function askUrl(){
    if(document.getElementById('srit-exec-ask'))return;
    var d=document.createElement('div');d.id='srit-exec-ask';
    d.style.cssText='position:fixed;inset:0;z-index:2147483646;background:#eef2f8;display:flex;align-items:center;justify-content:center;padding:20px;font:15px/1.5 system-ui,sans-serif;color:#1b2440';
    d.innerHTML='<div style="max-width:460px;width:100%;background:#fff;border:1px solid #d5dcee;border-radius:14px;padding:20px">'+
      '<h2 style="margin:0 0 6px;font-size:20px">Hubungkan ke server</h2>'+
      '<p style="margin:0 0 12px;color:#5a6785">Tempel alamat web app Apps Script (berakhiran <b>/exec</b>). Cukup sekali di perangkat ini.</p>'+
      '<input id="srit-exec-in" placeholder="https://script.google.com/macros/s/…/exec" style="width:100%;box-sizing:border-box;padding:10px;border:1px solid #b9c3de;border-radius:8px;font-size:14px">'+
      '<div id="srit-exec-err" style="color:#c62828;font-size:13px;min-height:18px;margin-top:6px"></div>'+
      '<button id="srit-exec-ok" style="width:100%;padding:10px;border:0;border-radius:8px;background:#1c6ef2;color:#fff;font-size:15px;font-weight:600">Simpan &amp; Mulai</button></div>';
    (document.body||document.documentElement).appendChild(d);
    document.getElementById('srit-exec-ok').onclick=function(){
      var v=document.getElementById('srit-exec-in').value.trim();
      if(!valid(v)){document.getElementById('srit-exec-err').textContent='Alamat harus berbentuk https://script.google.com/macros/s/…/exec';return;}
      ls('s',KEY,v);location.reload();
    };
  }
  window.SRIT_ChangeExec=function(){ls('d',KEY);location.reload();};
  document.addEventListener('DOMContentLoaded',function(){if(!execUrl())askUrl();});

  function post(fn,args){
    var url=execUrl();
    if(!url){askUrl();return Promise.reject(new Error('Alamat server belum diisi'));}
    var ctl=('AbortController' in window)?new AbortController():null,tm=ctl&&setTimeout(function(){ctl.abort();},90000);
    return fetch(url,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({fn:fn,args:args||[]}),redirect:'follow',signal:ctl?ctl.signal:undefined})
      .then(function(r){if(tm)clearTimeout(tm);if(!r.ok)throw new Error('Server menjawab '+r.status);return r.text();})
      .then(function(t){var j;try{j=JSON.parse(t);}catch(e){throw new Error('Jawaban server tidak valid (apakah deployment sudah "Versi baru" dan akses "Siapa saja"?)');}return j;})
      .catch(function(e){if(tm)clearTimeout(tm);throw new Error(e&&e.name==='AbortError'?'Server terlalu lama menjawab':(e&&e.message==='Failed to fetch'?'Tidak terhubung ke server (periksa internet / alamat /exec)':(e&&e.message)||'Gagal menghubungi server'));});
  }
  // pengganti google.script.run (rantai withSuccessHandler/withFailureHandler, lalu nama fungsi)
  function chain(ok,fail){
    return new Proxy({},{get:function(_,name){
      if(name==='withSuccessHandler')return function(h){return chain(h,fail);};
      if(name==='withFailureHandler')return function(h){return chain(ok,h);};
      if(name==='withUserObject')return function(){return chain(ok,fail);};
      if(typeof name!=='string'||name==='then')return undefined;
      return function(){var a=Array.prototype.slice.call(arguments);
        post(name,a).then(function(r){if(ok)ok(r);},function(e){if(fail)fail(e);else if(window.console)console.error(name,e);});};
    }});
  }
  window.google=window.google||{};window.google.script={run:chain(null,null),host:{close:function(){},setHeight:function(){},setWidth:function(){}}};
})();
