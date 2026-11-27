#!/usr/bin/env python3
"""
Monta o site do OpenPod no formato "documentacao" (sidebar + submenus + busca).

Reaproveita o CONTEUDO do gera_site.py (as funcoes que devolvem o texto de cada
pagina, em PT e EN) e troca o ARMAZENAMENTO: em vez de paineis escondidos por
hash numa pagina so, cada assunto vira uma PAGINA, com a sidebar fixa.

Uso:
  python3 tools/gera_site_docs.py --entrada docs/index.html --saida docs/index.html
  python3 tools/gera_site_docs.py --entrada docs/index.html --saida .tmp/site.html
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gera_site as g  # noqa: E402  (o conteudo vem de la)


CSS_EXTRA = r"""
.lateral{position:fixed;top:0;left:0;width:var(--side);height:100vh;overflow-y:auto;
  background:var(--card);border-right:1px solid var(--line);padding:20px 18px 40px;z-index:30}
.lateral .marca{display:block;font-size:21px;font-weight:800;letter-spacing:-.02em;
  color:var(--ink);text-decoration:none;margin-bottom:2px}
.lateral .submarca{display:block;color:var(--soft);font-size:12.5px;margin-bottom:16px}
.lateral h4{font:600 11px "IBM Plex Mono",monospace;text-transform:uppercase;letter-spacing:.09em;
  color:var(--soft);margin:20px 0 7px}
.lateral ul{list-style:none;padding:0;margin:0}
.lateral a{display:block;padding:6px 10px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14.5px}
.lateral a:hover{background:var(--bg)}
.lateral a.atual{background:var(--bg);box-shadow:inset 0 0 0 1.5px var(--accent);font-weight:700}
.lateral .externo::after{content:" ↗";font-size:11px;color:var(--soft)}
.busca{margin:0 0 8px}
.busca input{width:100%;font:14px Archivo,system-ui,sans-serif;padding:8px 10px;border-radius:9px;
  border:1.5px solid var(--line);background:var(--bg);color:var(--ink)}
.busca input:focus{outline:none;border-color:var(--accent)}
.resultados{display:none;margin:2px 0 10px;border:1px solid var(--line);border-radius:10px;background:var(--card);overflow:hidden}
.resultados.on{display:block}
.resultados a{display:block;padding:7px 10px;font-size:13.5px;text-decoration:none;color:var(--ink)}
.resultados a:hover{background:var(--bg)}
.resultados .vazio{padding:9px 10px;color:var(--soft);font-size:13px}
.idiomas{display:flex;gap:5px;margin:10px 0 0}
.idiomas button{font:600 12px "IBM Plex Mono",monospace;background:transparent;color:var(--soft);
  border:1.5px solid var(--line);border-radius:7px;padding:4px 9px;cursor:pointer}
.idiomas button[aria-pressed="true"]{color:var(--ink);border-color:var(--accent)}
.conteudo{margin-left:var(--side);padding:28px 40px 90px;max-width:900px}
.abrir{display:none}
@media (max-width:940px){
  .lateral{transform:translateX(-100%);transition:transform .2s}
  .lateral.visivel{transform:none;box-shadow:0 0 0 100vmax rgba(0,0,0,.35)}
  .conteudo{margin-left:0;padding:20px 16px 80px}
  .abrir{display:inline-block;margin-bottom:14px}
}
.pagina{display:none}
.pagina.ativa{display:block}
.jogadores{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:16px;margin:20px 0}
.jogador{display:block;text-decoration:none;color:inherit;background:var(--card);
  border:1px solid var(--line);border-radius:14px;padding:16px;text-align:center}
.jogador:hover{border-color:var(--accent)}
.jogador img{width:100%;max-width:180px;border-radius:12px;display:block;margin:0 auto 12px}
.jogador .nome{font-weight:700;display:block;margin-bottom:5px}
.jogador .detalhe{font-size:13px;color:var(--soft);display:block;margin-top:7px}
.etiqueta{display:inline-block;font:600 11px "IBM Plex Mono",monospace;padding:2px 9px;border-radius:999px;
  border:1.5px solid var(--line);color:var(--soft)}
.etiqueta.ok{border-color:var(--ok);color:var(--ok)}
.etiqueta.aviso{border-color:var(--talvez);color:var(--talvez)}
.etiqueta.novo{border-color:var(--accent);color:var(--accent)}
.anuncios{list-style:none;padding:0;margin:14px 0}
.anuncios li{border-top:1px solid var(--line);padding:10px 0}
.anuncios li:first-child{border-top:none}
.anuncios .quando{font:600 12px "IBM Plex Mono",monospace;color:var(--soft);margin-right:8px}
.passo-n{counter-reset:p;list-style:none;padding:0;margin:14px 0}
.passo-n li{counter-increment:p;position:relative;padding:6px 0 6px 38px}
.passo-n li::before{content:counter(p);position:absolute;left:0;top:6px;width:24px;height:24px;
  border-radius:50%;background:var(--accent);color:#fff;font:700 13px "IBM Plex Mono",monospace;
  display:flex;align-items:center;justify-content:center}
th{text-align:left;border-top:1px solid var(--line);padding:9px 6px;font-size:13px;color:var(--soft);
  text-transform:uppercase;letter-spacing:.05em}
.rodape{margin-top:60px;color:var(--soft);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
.rodape a{color:var(--soft)}
.topo{float:right;font-size:12px}
"""

JS_EXTRA = r"""
function aplicarIdioma(l){
  document.documentElement.setAttribute("data-lang", l);
  document.documentElement.lang = l === "pt" ? "pt-BR" : "en";
  try { localStorage.setItem("openpod-lang", l); } catch (e) {}
  document.querySelectorAll(".idiomas button").forEach(function(b){
    b.setAttribute("aria-pressed", b.dataset.l === l ? "true" : "false");
  });
  document.querySelectorAll(".idioma-rot").forEach(function(e){
    e.textContent = (l === "pt") ? e.dataset.pt : e.dataset.en;
  });
  marcarPagina(paginaAtual());
}
function paginaAtual(){
  var h = (location.hash || "").replace(/^#/, "");
  if (!h) return "inicio";
  if (h.indexOf("/") > 0) h = h.split("/")[0];
  return h || "inicio";
}
function marcarPagina(p){
  var en = document.documentElement.getAttribute("data-lang") === "en";
  var alvo = (en ? "p-en-" : "p-") + p;
  document.querySelectorAll(".pagina").forEach(function(e){
    e.classList.toggle("ativa", e.id === alvo);
  });
  document.querySelectorAll(".lateral a[data-p]").forEach(function(a){
    a.classList.toggle("atual", a.dataset.p === p);
  });
  try { history.replaceState(null, "", "#" + p); } catch (e) { location.hash = p; }
  window.scrollTo(0, 0);
}
function ir(p){ marcarPagina(p); }
function menuAberto(){
  var l = document.querySelector(".lateral");
  if (l) l.classList.toggle("visivel");
}
var INDICE = [];
function montarIndice(){
  INDICE = [];
  document.querySelectorAll(".lateral a[data-p]").forEach(function(a){
    var t = a.textContent.trim();
    if (t) INDICE.push({t: t.toLowerCase(), p: a.dataset.p});
  });
}
function buscar(q){
  var r = document.getElementById("resultados");
  if (!r) return;
  q = (q || "").trim().toLowerCase();
  if (q.length < 2) { r.classList.remove("on"); r.innerHTML = ""; return; }
  var achados = INDICE.filter(function(i){ return i.t.indexOf(q) >= 0; }).slice(0, 12);
  r.innerHTML = "";
  if (!achados.length) {
    r.innerHTML = '<div class="vazio">' + (document.documentElement.getAttribute("data-lang") === "pt"
      ? "Nada encontrado." : "Nothing found.") + "</div>";
  } else {
    achados.forEach(function(i){
      var a = document.createElement("a");
      a.href = "#" + i.p;
      a.textContent = i.t.charAt(0).toUpperCase() + i.t.slice(1);
      a.onclick = function(){ ir(i.p); r.classList.remove("on"); };
      r.appendChild(a);
    });
  }
  r.classList.add("on");
}
window.addEventListener("hashchange", function(){ marcarPagina(paginaAtual()); });
document.addEventListener("DOMContentLoaded", function(){
  montarIndice();
  // preenche os rotulos trocados (sidebar, rodape) e marca a pagina certa
  aplicarIdioma(document.documentElement.getAttribute("data-lang"));
});
"""


def menu() -> str:
    return """<nav class="lateral" aria-label="Menu">
  <a class="marca" href="#inicio">OpenPod</a>
  <span class="submarca idioma-rot" data-pt="Firmware novo para players de música" data-en="New firmware for music players"></span>

  <div class="busca">
    <input type="search" id="campo-busca" placeholder="Buscar" aria-label="Buscar"
           oninput="buscar(this.value)">
    <div class="resultados" id="resultados"></div>
  </div>

  <div class="idiomas">
    <button type="button" data-l="pt" onclick="aplicarIdioma('pt')">PT</button>
    <button type="button" data-l="en" onclick="aplicarIdioma('en')">EN</button>
  </div>

  <h4 class="idioma-rot" data-pt="Navegar" data-en="Browse"></h4>
  <ul>
    <li><a href="#inicio" data-p="inicio"><span class="idioma-rot" data-pt="Início" data-en="Home"></span></a></li>
    <li><a href="#instalar" data-p="instalar"><span class="idioma-rot" data-pt="Instalar" data-en="Install"></span></a></li>
    <li><a href="#sistemas" data-p="sistemas"><span class="idioma-rot" data-pt="Os sistemas" data-en="The systems"></span></a></li>
    <li><a href="#recursos" data-p="recursos"><span class="idioma-rot" data-pt="Recursos" data-en="Features"></span></a></li>
  </ul>

  <h4 class="idioma-rot" data-pt="Aparelhos" data-en="Players"></h4>
  <ul>
    <li><a href="#compat" data-p="compat"><span class="idioma-rot" data-pt="Compatibilidade" data-en="Compatibility"></span></a></li>
    <li><a href="#recuperar" data-p="recuperar"><span class="idioma-rot" data-pt="Recovery" data-en="Recovery"></span></a></li>
  </ul>

  <h4 class="idioma-rot" data-pt="O Tune" data-en="The Tune"></h4>
  <ul>
    <li><a href="#tune" data-p="tune"><span class="idioma-rot" data-pt="O que ele faz" data-en="What it does"></span></a></li>
    <li><a href="#loja" data-p="loja"><span class="idioma-rot" data-pt="A loja (StorePod)" data-en="The store (StorePod)"></span></a></li>
  </ul>

  <h4 class="idioma-rot" data-pt="Mais" data-en="More"></h4>
  <ul>
    <li><a href="#historico" data-p="historico"><span class="idioma-rot" data-pt="Histórico" data-en="History"></span></a></li>
    <li><a href="#sobre" data-p="sobre"><span class="idioma-rot" data-pt="Sobre" data-en="About"></span></a></li>
    <li><a href="#legacy" data-p="legacy"><span class="idioma-rot" data-pt="Método antigo" data-en="Old method"></span></a></li>
    <li><a href="https://github.com/zeroproj/OpenPod/issues" class="externo"><span class="idioma-rot" data-pt="Suporte" data-en="Support"></span></a></li>
  </ul>
</nav>"""


def home_nova(img) -> tuple:
    """A home no formato rockslop: botao grande, grade de sistemas, tabela, anuncios."""
    pt = f'''<h1>OpenPod</h1>
<p class="sub">Um firmware novo para players de música com o chip <strong>Smartlink SL6801</strong>: visual limpo, foco em música, feito a partir do sistema de fábrica.</p>
<p class="sub"><small>Testado no <strong>Ligenai GN-438</strong> e no <strong>GN-408</strong>.</small></p>
<div class="botoes">
  <a class="btn grande" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">Baixar o OpenPod Tune para macOS</a>
  <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Baixar para Windows (.exe)</a>
  <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Baixar para Linux (.tar.gz)</a>
</div>
<p class="sub"><small><span class="linha sys">System 5.3</span> <span class="linha rb">RockBox 5.3</span> <span class="linha prog">Tune 0.4.0</span> · 27/11/2026</small></p>

<h2>Dois sistemas, você escolhe</h2>
<div class="jogadores">
  <a class="jogador" href="#sistemas">
    <img src="{img["system"]}" alt="OpenPod System 5.3: nove ícones e, embaixo, o cartão com o nome da música">
    <span class="nome">OpenPod System</span>
    <span class="etiqueta ok">Released</span>
    <span class="detalhe">O sistema de fábrica, melhorado. Rádio, gravador, vídeo, Bluetooth, jogos e Atualizar por SD.</span>
  </a>
  <a class="jogador" href="#sistemas">
    <img src="{img["rockbox"]}" alt="OpenPod RockBox: menu com os ícones do OpenPod e o cartão do player">
    <span class="nome">OpenPod RockBox</span>
    <span class="etiqueta ok">Released</span>
    <span class="detalhe">O Rockbox para o SL6801, com o visual OpenPod. Mais formatos de áudio, estável e leve.</span>
  </a>
</div>

<table>
  <thead><tr><th>Sistema</th><th>Versão</th><th>Para quem é</th></tr></thead>
  <tbody>
    <tr><td>OpenPod System</td><td><span class="etiqueta ok">5.3</span></td><td>Quem quer o player completo — rádio, gravador, vídeo, Bluetooth — com a cara nova em cima</td></tr>
    <tr><td>OpenPod RockBox</td><td><span class="etiqueta ok">5.3.822b9f5e99</span></td><td>Quem quer música e só, com mais formatos de áudio e uma loja de apps</td></tr>
    <tr><td>OpenPod Tune</td><td><span class="etiqueta novo">0.4.0</span></td><td>O programa que instala, atualiza e guarda as cópias de segurança</td></tr>
  </tbody>
</table>

<h2>O que o OpenPod traz</h2>
<ul>
  <li>Logo do OpenPod na abertura e fundo preto nas telas.</li>
  <li>Barra superior com degradê: relógio, <strong>OpenPod</strong> e bateria alinhados.</li>
  <li>Ícones novos na tela inicial, sem nomes, com <strong>moldura branca</strong> no item selecionado.</li>
  <li><strong>Capa do álbum</strong> na tela Tocando Agora, lida do próprio MP3.</li>
  <li><strong>Menu Aplicativos</strong> com Despertador, Imagem e <strong>jogos</strong>.</li>
  <li><strong>Atualizar por SD</strong>: as próximas versões entram pelo cartão, sem computador.</li>
</ul>
<div class="nota">O <strong>OpenPod Tune</strong> é quem faz tudo isso: instala, atualiza, guarda a cópia de segurança antes de gravar e avisa quando há versão nova. <a href="#tune">Ver o que ele faz</a>.</div>

<h2>Como instalar</h2>
<ol class="passo-n">
  <li>Baixe o <strong>OpenPod Tune</strong> (macOS, Windows ou Linux).</li>
  <li>Escolha o sistema — no RockBox, escolha também o idioma.</li>
  <li>Coloque o player no <strong>modo de gravação</strong> (segure o volume para baixo e ligue o cabo).</li>
  <li>Clique em <strong>Instalar</strong> e espere a tela <strong>Pronto</strong>.</li>
</ol>
<p><small>Tem um player sem o botão RESET? <a href="#instalar">Há dois jeitos</a> de entrar no modo de gravação.</small></p>

<h2>Últimas novidades</h2>
<ul class="anuncios">
  <li><span class="quando">27/11/2026</span> <strong>OpenPod Tune 0.4.0</strong> — o cartão passa a guardar a versão instalada, o Tune escolhe sozinho entre cartão e Recovery, avisa de versão nova e respeita o idioma escolhido no RockBox. <a href="#tune">Ver</a></li>
  <li><span class="quando">26/11/2026</span> <strong>OpenPod RockBox 5.3</strong> — nova numeração e de volta os recursos do próprio sistema. <a href="#sistemas">Ver</a></li>
  <li><span class="quando">26/11/2026</span> <strong>OpenPod System 5.3</strong> — renumeração da 3.5, mesmas funções. <a href="#sistemas">Ver</a></li>
</ul>
<a href="#historico">Ver o histórico inteiro</a>'''

    en = f'''<h1>OpenPod</h1>
<p class="sub">A new firmware for music players with the <strong>Smartlink SL6801</strong> chip: a clean look, a focus on music, built on top of the stock system.</p>
<p class="sub"><small>Tested on the <strong>Ligenai GN-438</strong> and the <strong>GN-408</strong>.</small></p>
<div class="botoes">
  <a class="btn grande" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">Get OpenPod Tune for macOS</a>
  <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Get it for Windows (.exe)</a>
  <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Get it for Linux (.tar.gz)</a>
</div>
<p class="sub"><small><span class="linha sys">System 5.3</span> <span class="linha rb">RockBox 5.3</span> <span class="linha prog">Tune 0.4.0</span> · 2026-11-27</small></p>

<h2>Two systems, you choose</h2>
<div class="jogadores">
  <a class="jogador" href="#sistemas">
    <img src="{img["system"]}" alt="OpenPod System 5.3: nine icons and, below, the card with the song name">
    <span class="nome">OpenPod System</span>
    <span class="etiqueta ok">Released</span>
    <span class="detalhe">The stock system, improved. Radio, recorder, video, Bluetooth, games and Update via SD.</span>
  </a>
  <a class="jogador" href="#sistemas">
    <img src="{img["rockbox"]}" alt="OpenPod RockBox: menu with the OpenPod icons and the player card">
    <span class="nome">OpenPod RockBox</span>
    <span class="etiqueta ok">Released</span>
    <span class="detalhe">Rockbox for the SL6801, with the OpenPod look. More audio formats, stable and light.</span>
  </a>
</div>

<table>
  <thead><tr><th>System</th><th>Version</th><th>Who it is for</th></tr></thead>
  <tbody>
    <tr><td>OpenPod System</td><td><span class="etiqueta ok">5.3</span></td><td>Those who want the complete player — radio, recorder, video, Bluetooth — with a new face on it</td></tr>
    <tr><td>OpenPod RockBox</td><td><span class="etiqueta ok">5.3.822b9f5e99</span></td><td>Those who want music and only that, with more audio formats and an app store</td></tr>
    <tr><td>OpenPod Tune</td><td><span class="etiqueta novo">0.4.0</span></td><td>The program that installs, updates and keeps the backups</td></tr>
  </tbody>
</table>

<h2>What OpenPod brings</h2>
<ul>
  <li>OpenPod logo on boot and a black background on the screens.</li>
  <li>Top bar with a gradient: clock, <strong>OpenPod</strong> and battery lined up.</li>
  <li>New icons on the home screen, no labels, with a <strong>white frame</strong> on the selected one.</li>
  <li><strong>Album art</strong> on the Now Playing screen, read from the MP3 itself.</li>
  <li><strong>Apps menu</strong> with Alarm, Image and <strong>games</strong>.</li>
  <li><strong>Update via SD</strong>: new versions arrive through the card, no computer needed.</li>
</ul>
<div class="nota"><strong>OpenPod Tune</strong> is what does all of it: it installs, updates, takes the backup before writing and tells you when there is a new version. <a href="#tune">See what it does</a>.</div>

<h2>How to install</h2>
<ol class="passo-n">
  <li>Download <strong>OpenPod Tune</strong> (macOS, Windows or Linux).</li>
  <li>Pick the system — on RockBox, also pick the language.</li>
  <li>Put the player in <strong>recovery mode</strong> (hold volume down and plug the cable in).</li>
  <li>Click <strong>Install</strong> and wait for the <strong>Done</strong> screen.</li>
</ol>
<p><small>Got a player with no RESET button? There are <a href="#instalar">two ways</a> into recovery mode.</small></p>

<h2>Latest announcements</h2>
<ul class="anuncios">
  <li><span class="quando">2026-11-27</span> <strong>OpenPod Tune 0.4.0</strong> — the card now keeps the installed version, Tune picks by itself between the card and Recovery, tells you about new versions and respects the language you pick for RockBox. <a href="#tune">See</a></li>
  <li><span class="quando">2026-11-26</span> <strong>OpenPod RockBox 5.3</strong> — new numbering and the system's own tools are back. <a href="#sistemas">See</a></li>
  <li><span class="quando">2026-11-26</span> <strong>OpenPod System 5.3</strong> — renumbering of 3.5, same features. <a href="#sistemas">See</a></li>
</ul>
<a href="#historico">See the full history</a>'''
    return pt, en


def sistemas(img) -> tuple:
    """A pagina dos sistemas: as duas opcoes, lado a lado, com o que cada uma tem."""
    pt = f'''<h1>Os sistemas</h1>
<p class="sub">São <strong>dois sistemas</strong> para o mesmo aparelho, e dá para trocar de um para o outro quando quiser. O Tune refaz a instalação inteira, e as suas músicas no cartão ficam lá.</p>

<div class="jogadores" style="margin:24px 0">
  <div class="jogador">
    <img src="{img["system"]}" alt="OpenPod System 5.3: nove ícones e, embaixo, o cartão com o nome da música">
    <span class="nome">OpenPod System</span>
    <span class="etiqueta ok">5.3</span>
    <span class="detalhe">O sistema de fábrica, melhorado. Rádio FM, gravador, vídeo, Bluetooth, jogos e Atualizar por SD. Agora com a música que está tocando na tela inicial.</span>
  </div>
  <div class="jogador">
    <img src="{img["rockbox"]}" alt="OpenPod RockBox: menu com os ícones do OpenPod e o cartão do player">
    <span class="nome">OpenPod RockBox</span>
    <span class="etiqueta ok">5.3.822b9f5e99</span>
    <span class="detalhe">O Rockbox para o SL6801, com o visual OpenPod e o seu idioma. Mais formatos de áudio, estável e leve. Apps e jogos testados chegam aos poucos.</span>
  </div>
</div>

<table>
  <thead><tr><th></th><th>OpenPod System</th><th>OpenPod RockBox</th></tr></thead>
  <tbody>
    <tr><td>Funções de fábrica</td><td>TODAS: rádio, gravador, vídeo, Bluetooth</td><td>Só música</td></tr>
    <tr><td>Jogos</td><td>Sim, no menu Aplicativos</td><td>Vêm pela StorePod, testados</td></tr>
    <tr><td>Capa do álbum</td><td>Sim, lida do MP3</td><td>Em beta (a 6.0 traz)</td></tr>
    <tr><td>Idioma</td><td>Português</td><td>50 idiomas, com o tema OpenPod</td></tr>
    <tr><td>Atualiza pelo cartão</td><td>Sim (o <code>update.up</code>)</td><td>Sim (a pasta <code>.rockbox</code>)</td></tr>
  </tbody>
</table>

<div class="nota"><strong>Se algo der errado</strong>, a <a href="#recuperar">Recuperação</a> traz o aparelho de volta ao firmware de fábrica, e o Recovery (ORS) deixa você voltar ao OpenPod depois só com o cartão.</div>'''

    en = f'''<h1>The systems</h1>
<p class="sub">There are <strong>two systems</strong> for the same player, and you can switch from one to the other whenever you want. Tune redoes the whole install, and the music on your card stays where it is.</p>

<div class="jogadores" style="margin:24px 0">
  <div class="jogador">
    <img src="{img["system"]}" alt="OpenPod System 5.3: nine icons and, below, the card with the song name">
    <span class="nome">OpenPod System</span>
    <span class="etiqueta ok">5.3</span>
    <span class="detalhe">The stock system, improved. FM radio, recorder, video, Bluetooth, games and Update via SD. Now with the playing song on the home screen.</span>
  </div>
  <div class="jogador">
    <img src="{img["rockbox"]}" alt="OpenPod RockBox: menu with the OpenPod icons and the player card">
    <span class="nome">OpenPod RockBox</span>
    <span class="etiqueta ok">5.3.822b9f5e99</span>
    <span class="detalhe">Rockbox for the SL6801, with the OpenPod look and your language. More audio formats, stable and light. Tested apps and games come in little by little.</span>
  </div>
</div>

<table>
  <thead><tr><th></th><th>OpenPod System</th><th>OpenPod RockBox</th></tr></thead>
  <tbody>
    <tr><td>Stock features</td><td>ALL of them: radio, recorder, video, Bluetooth</td><td>Music only</td></tr>
    <tr><td>Games</td><td>Yes, in the Apps menu</td><td>They come through StorePod, tested</td></tr>
    <tr><td>Album art</td><td>Yes, read from the MP3</td><td>In beta (6.0 brings it)</td></tr>
    <tr><td>Language</td><td>Portuguese</td><td>50 languages, with the OpenPod theme</td></tr>
    <tr><td>Updates through the card</td><td>Yes (the <code>update.up</code>)</td><td>Yes (the <code>.rockbox</code> folder)</td></tr>
  </tbody>
</table>

<div class="nota"><strong>If something goes wrong</strong>, <a href="#recuperar">Recovery</a> brings the player back to the stock firmware, and Recovery (ORS) lets you come back to OpenPod later with the card alone.</div>'''
    return pt, en


def loja() -> tuple:
    pt = '''<h1>A loja (StorePod)</h1>
<p class="sub">Dentro do OpenPod Tune tem uma lojinha de temas, apps e jogos <strong>testados</strong> para o OpenPod RockBox.</p>

<div class="grade">
  <div class="card"><h4>Instalar pelo cartão</h4><p>Os itens vão para a pasta <code>.rockbox</code> do cartão. Não precisa reinstalar o sistema e não precisa de computador.</p></div>
  <div class="card"><h4>Só o que foi testado</h4><p>Cada item entra na loja depois de ser testado num aparelho de verdade. App que trava não entra.</p></div>
  <div class="card"><h4>Requisitos</h4><p>Cada item pode pedir uma versão mínima do RockBox. O Tune compara com a versão instalada (que fica no cartão) e recusa, com mensagem clara, quando não dá.</p></div>
  <div class="card"><h4>Atualização junto</h4><p>Quando o tema OpenPod mudar, a atualização chega pela loja — sem reinstalar nada.</p></div>
</div>

<h2>O primeiro item</h2>
<div class="card"><h4>Tema OpenPod</h4><p>O tema que o RockBox já usa. É um <strong>item do sistema</strong>: aparece como <strong>Instalado</strong> na loja, sem botão de Remover — porque remover o tema deixaria o RockBox sem o visual do OpenPod.</p></div>

<div class="nota">A loja vem no <strong>OpenPod Tune</strong>. Para ver os itens, abra o Tune e vá na aba da <strong>StorePod</strong>.</div>'''

    en = '''<h1>The store (StorePod)</h1>
<p class="sub">Inside OpenPod Tune there is a little shop of themes, apps and <strong>tested</strong> games for OpenPod RockBox.</p>

<div class="grade">
  <div class="card"><h4>Installed through the card</h4><p>Items go into the card's <code>.rockbox</code> folder. No need to reinstall the system and no need for a computer.</p></div>
  <div class="card"><h4>Only what was tested</h4><p>Every item joins the shop after being tested on a real player. An app that freezes does not go in.</p></div>
  <div class="card"><h4>Requirements</h4><p>Each item may ask for a minimum RockBox version. Tune compares it with the installed version (which lives on the card) and refuses, with a clear message, when it does not work out.</p></div>
  <div class="card"><h4>Updates along with it</h4><p>When the OpenPod theme changes, the update arrives through the shop — without reinstalling anything.</p></div>
</div>

<h2>The first item</h2>
<div class="card"><h4>OpenPod theme</h4><p>The theme RockBox already uses. It is a <strong>system item</strong>: it shows as <strong>Installed</strong> in the shop, with no Remove button — removing the theme would leave RockBox without the OpenPod look.</p></div>

<div class="nota">The shop comes with <strong>OpenPod Tune</strong>. To see the items, open Tune and go to the <strong>StorePod</strong> tab.</div>'''
    return pt, en


def instalar_nova(img) -> tuple:
    pt = '''<h1>Instalar</h1>
<p class="sub">O jeito mais fácil é o <strong>OpenPod Tune</strong>. Se preferir fazer à mão, o caminho manual está mais abaixo.</p>

<div class="card"><h3>1. Baixe o Tune</h3>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">macOS (.dmg)</a><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Windows (.exe)</a><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Linux (.tar.gz)</a></div>
<p><small><strong>macOS:</strong> na primeira vez, se o macOS bloquear, abra em Ajustes do Sistema → Privacidade e Segurança → "Abrir assim mesmo". O Tune pede a senha do Mac para falar com o player. <strong>Windows:</strong> se aparecer "O Windows protegeu o computador", clique em "Mais informações → Executar assim mesmo". Não precisa instalar driver. <strong>Linux:</strong> descompacte, rode uma vez <code>sh instalar-regra.sh</code> e abra o <code>./openpod-tune</code>.</small></p></div>

<div class="card"><h3>2. Coloque o player no modo de gravação</h3>
<p>Conecte o player ao computador pelo cabo USB. Há <strong>dois jeitos</strong>:</p>
<h4 class="sub-h">Com o botão RESET</h4>
<ol type="a">
  <li>Com um <strong>clipe de papel desdobrado</strong> (ou outro objeto fino e adequado), pressione suavemente o botão <strong>RESET</strong>, no pequeno orifício na lateral do aparelho.</li>
  <li>Pressione e mantenha pressionado o botão <strong>VOL para baixo</strong> (diminuir volume).</li>
  <li>Enquanto mantém o volume pressionado, retire o clipe do botão RESET.</li>
  <li><strong>Continue segurando o volume para baixo por uns 3 segundos.</strong></li>
</ol>
<h4 class="sub-h">Se o seu player não tem o botão RESET</h4>
<ol type="a">
  <li><strong>Desligue</strong> o player.</li>
  <li><strong>Segure</strong> o botão <strong>VOL para baixo</strong> (diminuir volume).</li>
  <li><strong>Ligue o cabo USB</strong>, sem soltar o volume.</li>
</ol>
<p>A tela do aparelho fica <strong>preta</strong> e o computador reconhece o aparelho em modo de gravação.</p></div>

<div class="card"><h3>3. Instale</h3>
<p>No Tune, escolha o sistema (no RockBox, também o idioma) e clique em <strong>Instalar</strong>. Espere a tela <strong>Pronto</strong>, sem tirar o cabo.</p>
<p>O Tune faz o <strong>backup completo</strong> da flash antes de gravar. É por isso que ele pede a senha do administrador no macOS.</p></div>

<h2>Atualizar depois</h2>
<p>Depois da primeira instalação, tem <strong>duas formas</strong> — e o Tune te mostra as duas, com o que cada uma faz:</p>
<table>
  <thead><tr><th></th><th>Pelo cartão SD</th><th>Pelo Recovery</th></tr></thead>
  <tbody>
    <tr><td>Quando serve</td><td>Só a <strong>personalização</strong> mudou (o tema, os idiomas, os plugins)</td><td>O <strong>firmware</strong> mudou (uma versão nova de verdade)</td></tr>
    <tr><td>Precisa de computador</td><td>Não</td><td>Sim, com o cabo</td></tr>
    <tr><td>O que é gravado</td><td>Só a pasta do cartão</td><td>A flash inteira e a pasta do cartão</td></tr>
  </tbody>
</table>

<h2>Atualizar pelo cartão, à mão</h2>
<p>Quando só a personalização mudou, dá para atualizar sem o Tune e sem computador:</p>
<div class="card"><ol class="passo-n">
  <li>Baixe a versão mais recente (o botão no topo da página). O arquivo já vem com o nome certo: <code>update.up</code>.</li>
  <li>Copie o <code>update.up</code> para a <strong>raiz</strong> do cartão (fora de qualquer pasta).</li>
  <li>Coloque o cartão no aparelho e vá em <code>Config → Atualizar por SD → Sim</code>.</li>
  <li>O aparelho reinicia, atualiza e volta sozinho.</li>
  <li><strong>Apague o <code>update.up</code> do cartão.</strong> Se ficar lá, ele tenta atualizar toda vez que liga.</li>
</ol></div>

<h2>Primeira instalação à mão, pelo cabo no Windows</h2>
<p>Se preferir não usar o Tune, dá para gravar direto com o gravador do fabricante do chip (o <strong>Flashloader SL-DEV</strong>, que é da Shenju — não é do OpenPod). O passo a passo está na <a href="#legacy">página do método antigo</a>.</p>'''

    en = '''<h1>Install</h1>
<p class="sub">The easy way is <strong>OpenPod Tune</strong>. If you prefer to do it by hand, the manual path is further down.</p>

<div class="card"><h3>1. Download Tune</h3>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">macOS (.dmg)</a><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Windows (.exe)</a><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Linux (.tar.gz)</a></div>
<p><small><strong>macOS:</strong> the first time, if macOS blocks it, open it in System Settings → Privacy &amp; Security → "Open Anyway". Tune asks for your Mac password to talk to the player. <strong>Windows:</strong> if "Windows protected your PC" shows up, click "More info → Run anyway". No driver to install. <strong>Linux:</strong> unpack it, run <code>sh instalar-regra.sh</code> once, then open <code>./openpod-tune</code>.</small></p></div>

<div class="card"><h3>2. Put the player in recovery mode</h3>
<p>Connect the player to the computer with the USB cable. There are <strong>two ways</strong>:</p>
<h4 class="sub-h">With the RESET button</h4>
<ol type="a">
  <li>With an <strong>unfolded paper clip</strong> (or another thin, suitable object), press the <strong>RESET</strong> button gently, in the small hole on the side of the player.</li>
  <li>Press and hold the <strong>VOL down</strong> button (volume down).</li>
  <li>While holding the volume down, pull the clip out of the RESET button.</li>
  <li><strong>Keep holding volume down for about 3 seconds.</strong></li>
</ol>
<h4 class="sub-h">If your player has no RESET button</h4>
<ol type="a">
  <li><strong>Turn the player off.</strong></li>
  <li><strong>Hold</strong> the <strong>VOL down</strong> button (volume down).</li>
  <li><strong>Plug in the USB cable</strong>, without letting go of the volume.</li>
</ol>
<p>The player's screen stays <strong>black</strong> and the computer recognises the player in recovery mode.</p></div>

<div class="card"><h3>3. Install</h3>
<p>In Tune, pick the system (on RockBox, also the language) and click <strong>Install</strong>. Wait for the <strong>Done</strong> screen, without unplugging the cable.</p>
<p>Tune takes the <strong>full backup</strong> of the flash before writing. That is why it asks for the administrator password on macOS.</p></div>

<h2>Updating later</h2>
<p>After the first install there are <strong>two ways</strong> — and Tune shows you both, and what each one does:</p>
<table>
  <thead><tr><th></th><th>Through the SD card</th><th>Through Recovery</th></tr></thead>
  <tbody>
    <tr><td>When it applies</td><td>Only the <strong>customization</strong> changed (the theme, the languages, the plugins)</td><td>The <strong>firmware</strong> changed (a genuinely new version)</td></tr>
    <tr><td>Needs a computer</td><td>No</td><td>Yes, with the cable</td></tr>
    <tr><td>What gets written</td><td>Only the card folder</td><td>The whole flash and the card folder</td></tr>
  </tbody>
</table>

<h2>Updating through the card, by hand</h2>
<p>When only the customization changed, you can update without Tune and without a computer:</p>
<div class="card"><ol class="passo-n">
  <li>Download the newest version (the button at the top of the page). The file already has the right name: <code>update.up</code>.</li>
  <li>Copy <code>update.up</code> to the <strong>root</strong> of the card (not inside any folder).</li>
  <li>Put the card in the player and go to <code>Config → Update via SD → Yes</code>.</li>
  <li>The player restarts, updates and comes back on its own.</li>
  <li><strong>Delete <code>update.up</code> from the card.</strong> If it stays, it tries to update every time it turns on.</li>
</ol></div>

<h2>First install by hand, over the cable on Windows</h2>
<p>If you would rather not use Tune, you can write straight with the chip maker's own writer (the <strong>Flashloader SL-DEV</strong>, from Shenju — it is not from OpenPod). The steps are on the <a href="#legacy">old method page</a>.</p>'''
    return pt, en


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="docs/index.html")
    ap.add_argument("--saida", default="docs/index.html")
    a = ap.parse_args()

    html = Path(a.entrada).read_text(encoding="utf-8")
    img = g.imagens(html)
    faltando = [k for k in ("home", "system", "rockbox") if k not in img]
    if faltando:
        raise SystemExit(f"faltou as imagens: {faltando}")

    # as paginas: (id, funcao que devolve (pt, en))
    paginas = []
    paginas.append(("inicio", home_nova(img)))
    paginas.append(("instalar", instalar_nova(img)))
    paginas.append(("sistemas", sistemas(img)))
    paginas.append(("recursos", g.painel_recursos()))
    paginas.append(("tune", g.painel_tune(img)))
    paginas.append(("loja", loja()))
    paginas.append(("compat", g.painel_compat()))
    paginas.append(("historico", g.painel_historico()))
    paginas.append(("sobre", g.painel_sobre()))
    paginas.append(("legacy", g.painel_legacy()))

    # o "recuperar" usa o painel de compatibilidade (que ja tem o Recovery)
    paginas.append(("recuperar", g.painel_compat()))

    # o CSS: o do gera_site + o do layout de documentacao
    css = g.CSS.replace(":root{\n  --bg:#f6f5f2;", ":root{\n  --bg:#f6f5f2; --side:288px;") + CSS_EXTRA
    js = """
// o idioma guardado (ou o do sistema). Aplica SO o rotulo dos <html>, para o
// CSS ja esconder a lingua errada; o texto dos rotulos trocados e' preenchido
// no DOMContentLoaded, quando o DOM ja existe.
(function(){
  var l = null;
  try { l = localStorage.getItem("openpod-lang"); } catch (e) {}
  if (l !== "pt" && l !== "en") l = /^pt/i.test(navigator.language || "") ? "pt" : "en";
  document.documentElement.setAttribute("data-lang", l);
  document.documentElement.lang = l === "pt" ? "pt-BR" : "en";
  try { localStorage.setItem("openpod-lang", l); } catch (e) {}
})();
""" + JS_EXTRA

    pt_paginas = []
    en_paginas = []
    for pid, (pt, en) in paginas:
        # os ids do EN levam o prefixo "en-": o mesmo id nas duas linguas seria
        # HTML invalido e o JS ligaria as duas paginas juntas
        pt_paginas.append(f'<section class="pagina" id="p-{pid}">{pt}</section>')
        en_paginas.append(f'<section class="pagina" id="p-en-{pid}">{en}</section>')

    rodape = """<div class="rodape">
<p><a class="topo" href="#inicio"><span class="idioma-rot" data-pt="Voltar ao topo" data-en="Back to top"></span> ↑</a></p>
<p><span class="idioma-rot" data-pt="OpenPod é um projeto independente, sem ligação com a Smartlink, a Shenju ou o fabricante do aparelho. Jogos e kit de apps baseados no" data-en="OpenPod is an independent project, with no connection to Smartlink, Shenju or the player's manufacturer. Games and app kit based on"></span> <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>, <span class="idioma-rot" data-pt="de Dmitry Brant (MIT). " data-en="by Dmitry Brant (MIT). "></span><a href="#sobre"><span class="idioma-rot" data-pt="Créditos" data-en="Credits"></span></a>. <span class="idioma-rot" data-pt="Use por sua conta e risco." data-en="Use at your own risk."></span></p>
</div>"""
    rodape_en = ""

    saida = f"""<!doctype html>
<html lang="pt-BR" data-lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>OpenPod</title>
<meta name="description" content="OpenPod — dois sistemas para players com chip Smartlink SL6801 (Ligenai GN-438 e GN-408): o OpenPod System e o OpenPod RockBox, com o visual OpenPod.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>
<script>{js}</script>
</head>
<body>
{menu()}
<main class="conteudo">
<button type="button" class="abrir" onclick="menuAberto()">☰ Menu</button>
<div lang="pt">
{"".join(pt_paginas)}
{rodape}
</div>
<div lang="en">
{"".join(en_paginas)}
{rodape_en}
</div>
</main>
</body>
</html>
"""
    Path(a.saida).write_text(saida, encoding="utf-8")
    print(f"gerado {a.saida} ({len(saida)} bytes, {len(paginas)} paginas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
