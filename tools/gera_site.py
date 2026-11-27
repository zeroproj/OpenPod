#!/usr/bin/env python3
"""
Reformula o site do OpenPod: tudo VOLTADO AO OPENPOD TUNE.

Lê o docs/index.html atual (que é o que está no ar), pega as imagens e
reconstrói a página com esta direção:

  - o herói fala do TUNE (é ele que faz tudo), e não de "um firmware";
  - as seções são as ABAS DO TUNE (Instalar, StorePod, Recuperação, Backup,
    Diagnóstico, Compatibilidade);
  - os MÉTODOS MANUAIS antigos (Flashloader da Shenju, update.up copiado na
    mão, Recovery) vão para uma PÁGINA LEGACY dentro do site, que fica
    escondida do menu principal;
  - o histórico é separado por linha (System / RockBox / Tune).

O script é idempotente: roda sempre sobre o docs/index.html que está no ar
(que é a fonte de verdade das imagens e do texto antigo), e escreve o site
novo em --saida.

Uso:
  python3 tools/gera_site.py --entrada docs/index.html --saida docs/index_novo.html
"""

import argparse
import re
from pathlib import Path

CSS = r"""
:root{
  --bg:#f6f5f2; --card:#ffffff; --ink:#16181c; --soft:#5b6270; --line:#e2e0da;
  --accent:#2f6fe4; --warn-bg:#fff4e0; --warn-ink:#7a4a00; --code:#eeece6;
  --ok:#1f9d55; --talvez:#c07a00; --velho:#8a8578;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0e1013; --card:#171a1f; --ink:#eceef2; --soft:#9aa3b2; --line:#2a2f37;
    --accent:#6c9cff; --warn-bg:#2b2112; --warn-ink:#f2c37a; --code:#22262d;
  }
}
:root[data-theme="dark"]{
  --bg:#0e1013; --card:#171a1f; --ink:#eceef2; --soft:#9aa3b2; --line:#2a2f37;
  --accent:#6c9cff; --warn-bg:#2b2112; --warn-ink:#f2c37a; --code:#22262d;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 Archivo,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:900px;margin:0 auto;padding:40px 16px 90px}
h1{font-size:clamp(36px,7.6vw,60px);line-height:1.03;margin:0 0 14px;font-weight:800;letter-spacing:-.03em}
h2{font-size:26px;margin:58px 0 14px;font-weight:800;letter-spacing:-.01em}
h3{font-size:18px;margin:30px 0 8px;font-weight:700}
h4{font-size:16px;margin:0 0 8px}
p,li{color:var(--ink)}
.sub{color:var(--soft);font-size:19px;max-width:640px;line-height:1.55}
.ver{font-family:"IBM Plex Mono",monospace;font-size:13px;background:var(--code);padding:3px 9px;border-radius:6px;color:var(--soft);white-space:nowrap}
figure{margin:0}
.hero{display:grid;grid-template-columns:1fr 264px;gap:44px;align-items:center}
.tela{width:264px;max-width:100%;border-radius:18px;border:10px solid #1b1d21;box-shadow:0 22px 55px rgba(0,0,0,.28);display:block}
@media (max-width:720px){.hero{grid-template-columns:1fr}.hero figure{justify-self:center}}
ul.novo{padding-left:20px}
ul.novo li{margin:6px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 24px;margin:16px 0}
.botoes{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}
a.btn{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;padding:13px 20px;border-radius:11px;font-weight:700}
a.btn.sec{background:transparent;color:var(--accent);border:1.5px solid var(--accent)}
a.btn.ghost{background:transparent;color:var(--soft);border:1.5px solid var(--line)}
a{color:var(--accent)}
code{font-family:"IBM Plex Mono",monospace;font-size:14px;background:var(--code);padding:1px 6px;border-radius:5px}
ol.passos{padding-left:22px}
ol.passos>li{margin:10px 0}
.aviso{background:var(--warn-bg);color:var(--warn-ink);border-radius:13px;padding:15px 19px;margin:16px 0}
.aviso strong{color:inherit}
.nota{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:14px 18px;margin:16px 0;color:var(--soft)}
table{border-collapse:collapse;width:100%;font-size:15px}
td{border-top:1px solid var(--line);padding:9px 6px;vertical-align:top}
td:first-child{white-space:nowrap;font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--soft)}
footer{margin-top:70px;color:var(--soft);font-size:13px;border-top:1px solid var(--line);padding-top:18px}
.idioma{display:flex;justify-content:flex-end;gap:6px;margin-bottom:8px}
.idioma button{font:600 13px "IBM Plex Mono",monospace;background:transparent;color:var(--soft);border:1.5px solid var(--line);border-radius:8px;padding:5px 11px;cursor:pointer}
.idioma button[aria-pressed="true"]{color:var(--ink);border-color:var(--accent)}
.abas{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 6px}
.abas button{font:700 15px Archivo,system-ui,sans-serif;background:transparent;color:var(--soft);border:1.5px solid var(--line);border-radius:11px;padding:11px 15px;cursor:pointer;text-align:left}
.abas button small{display:block;font-weight:500;font-size:13px}
.abas button[aria-selected="true"]{color:var(--ink);border-color:var(--accent);background:var(--card)}
html[data-aba="novo"] .aba-atual{display:none}
html[data-aba="atual"] .aba-novo{display:none}
.ok{color:var(--ok);font-weight:700}.talvez{color:var(--talvez);font-weight:700}
.menu{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 30px;padding-bottom:12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
.menu a{font:700 15px Archivo,system-ui,sans-serif;color:var(--soft);text-decoration:none;padding:9px 13px;border-radius:10px}
.menu a[aria-current="page"]{color:var(--ink);background:var(--card);box-shadow:inset 0 0 0 1.5px var(--accent)}
html[data-pag] [data-painel]{display:none}
html[data-pag="inicio"] [data-painel="inicio"],
html[data-pag="tune"] [data-painel="tune"],
html[data-pag="instalar"] [data-painel="tune"],
html[data-pag="recursos"] [data-painel="recursos"],
html[data-pag="compat"] [data-painel="compat"],
html[data-pag="sobre"] [data-painel="sobre"]{display:block}
/* a pagina legacy e escondida do menu: se entra por #legacy, ela abre */
html[data-pag="legacy"] [data-painel="legacy"]{display:block}
html[data-pag="legacy"] .menu{display:none}
.grade{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:18px 0}
.grade .card{margin:0;padding:18px 20px}
.grade h4{margin-bottom:4px}
.grade p{font-size:14.5px;color:var(--soft);margin:4px 0 0}
.trilha{display:grid;gap:0;margin:20px 0;border-left:2px solid var(--line);padding-left:0}
.trilha .item{position:relative;padding:0 0 22px 26px}
.trilha .item:last-child{padding-bottom:0}
.trilha .item::before{content:"";position:absolute;left:-7px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--card);border:2px solid var(--line)}
.trilha .item.destaque::before{background:var(--accent);border-color:var(--accent)}
.trilha .quando{font:600 12px "IBM Plex Mono",monospace;color:var(--soft);letter-spacing:.02em}
.trilha .titulo{font-weight:700;margin:2px 0 3px}
.trilha .texto{font-size:14.5px;color:var(--soft)}
.tipos{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin:20px 0}
.tipos .card{margin:0;padding:20px 22px;display:flex;flex-direction:column}
.tipos .card h4{margin:2px 0 4px;font-size:19px}
.tipos .card h4 strong{font-weight:800}
.tipos .card p{font-size:14.5px;margin:8px 0 0}
.tipos .rotulo{font:600 11px "IBM Plex Mono",monospace;letter-spacing:.09em;text-transform:uppercase;color:var(--soft)}
.tipos .versoes{margin:2px 0 4px}
.tipos .detalhe{color:var(--soft);font-size:13.5px!important;margin-top:auto!important;padding-top:10px}
.tipos .card.tipo-sistema{border-top:3px solid var(--accent)}
.tipos .card.tipo-sistema .rotulo{color:var(--accent)}
.tipos .card.tipo-programa{border-top:3px solid var(--ok)}
.tipos .card.tipo-programa .rotulo{color:var(--ok)}
.linha{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:12px;padding:2px 8px;border-radius:999px;border:1.5px solid var(--line);color:var(--soft);margin-right:6px}
.linha.sys{border-color:var(--accent);color:var(--accent)}
.linha.rb{border-color:var(--ok);color:var(--ok)}
.linha.prog{border-color:var(--talvez);color:var(--talvez)}
.linhas{margin:22px 0}
.linha-bloco{margin:0 0 34px;padding:0 0 4px}
.linha-bloco .cabeca{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 4px}
.linha-bloco .cabeca h3{margin:0;font-size:21px}
.linha-bloco .cabeca .linha{margin:0;font-size:12px;font-weight:700}
.linha-bloco .intro{color:var(--soft);font-size:15px;margin:0 0 14px;max-width:720px}
.linha-bloco .grade{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.sistemas{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.sistemas figure{margin:0}
.sistemas img.tela{max-width:190px}
.sistemas figcaption{font-size:.95em;margin-top:10px}
@media(max-width:680px){.sistemas{grid-template-columns:1fr}}
.grupo{columns:2 260px;column-gap:30px;padding-left:20px}.grupo li{break-inside:avoid;margin:5px 0}
pre{background:var(--code);border-radius:11px;padding:13px 15px;overflow-x:auto;font:13px/1.55 "IBM Plex Mono",monospace;white-space:pre-wrap;word-break:break-all}
html[data-lang="pt"] [lang="en"]{display:none}
html[data-lang="en"] [lang="pt"]{display:none}
/* a pagina legacy tem um clima proprio, para ninguem confunda com o caminho novo */
.painel-legacy{--accent:#8a8578}
.painel-legacy .card{border-style:dashed}
.painel-legacy h2::after{content:" — método antigo";font:600 12px "IBM Plex Mono",monospace;color:var(--velho);vertical-align:middle;margin-left:8px;border:1.5px solid var(--velho);border-radius:999px;padding:2px 9px}
.aviso-legacy{background:transparent;color:var(--soft);border:1.5px dashed var(--velho);border-radius:13px;padding:15px 19px;margin:16px 0}
"""

JS = r"""
(function(){
  var l = null;
  try { l = localStorage.getItem("openpod-lang"); } catch (e) {}
  if (l !== "pt" && l !== "en") l = /^pt/i.test(navigator.language || "") ? "pt" : "en";
  document.documentElement.setAttribute("data-lang", l);
  document.documentElement.lang = l === "pt" ? "pt-BR" : "en";
})();
function idioma(l){
  document.documentElement.setAttribute("data-lang", l);
  document.documentElement.lang = l === "pt" ? "pt-BR" : "en";
  try { localStorage.setItem("openpod-lang", l); } catch (e) {}
  document.querySelectorAll(".idioma button").forEach(function(b){ b.setAttribute("aria-pressed", b.dataset.l === l); });
}
function aba(a){
  document.documentElement.setAttribute("data-aba", a);
  try { localStorage.setItem("openpod-aba", a); } catch (e) {}
  document.querySelectorAll(".abas button").forEach(function(b){ b.setAttribute("aria-selected", b.dataset.a === a); });
}
var ROTAS = {inicio:"inicio", tune:"tune", instalar:"tune", recursos:"recursos", compat:"compat",
             sobre:"sobre", legacy:"legacy"};
function pag(p){
  document.documentElement.setAttribute("data-pag", p);
  document.querySelectorAll(".menu a").forEach(function(a){ a.setAttribute("aria-current", a.dataset.p === p ? "page" : "false"); });
}
function rota(){
  var h = (location.hash || "").slice(1), p = ROTAS[h] || "inicio";
  pag(p);
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", rota);
document.addEventListener("DOMContentLoaded", function(){
  rota();
  idioma(document.documentElement.getAttribute("data-lang"));
  var a = null; try { a = localStorage.getItem("openpod-aba"); } catch (e) {}
  aba(a === "atual" ? "atual" : "novo");
});
"""


def imagens(html: str) -> dict:
    achadas = re.findall(r'<img class="tela" alt="([^"]*)" src="(data:image/png;base64,[^"]+)"', html)
    out = {}
    for alt, src in achadas:
        if alt.startswith("OpenPod home screen") or alt.startswith("Tela inicial do OpenPod:"):
            out["home"] = src
        elif alt.startswith("OpenPod System 5.3: nine") or alt.startswith("OpenPod System 5.3: nove"):
            out["system"] = src
        elif "OpenPod RockBox" in alt:
            out["rockbox"] = src
    return out


# --------------------------------------------------------------------------
# o conteúdo
# --------------------------------------------------------------------------

def painel_inicio(img):
    pt = f'''<section class="hero">
  <div>
    <h1>OpenPod</h1>
    <p class="sub">Um firmware novo para players de música com o chip <strong>Smartlink SL6801</strong>: visual limpo, foco em música, e feito a partir do sistema de fábrica.</p>
    <p class="sub"><small>Testado no <strong>Ligenai GN-438</strong> e no <strong>GN-408</strong>. <a href="#compat">Ver compatibilidade</a></small></p>
    <div class="botoes">
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">Baixar o Tune para macOS</a>
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Baixar o Tune para Windows</a>
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Baixar o Tune para Linux</a>
      <a class="btn sec" href="#instalar">Como instalar</a>
    </div>
  </div>
  <figure><img class="tela" alt="Tela inicial do OpenPod: barra com relógio, OpenPod e bateria; nove ícones escuros com símbolos coloridos, em grade, incluindo Aplicativos, o selecionado com moldura branca" src="{img["home"]}"></figure>
</section>

<h2 id="tipos">O que existe</h2>
<p>São <strong>três coisas</strong>, com nomes diferentes — e dá para confundir. O <strong>OpenPod</strong> é o
projeto. Dentro dele há <strong>dois sistemas</strong> para o seu aparelho, e <strong>um programa</strong> que
instala, atualiza e cuida dos dois.</p>

<div class="tipos">
  <div class="card tipo-sistema">
    <div class="rotulo">Sistema 1</div>
    <h4>OpenPod <strong>System</strong></h4>
    <div class="versoes"><span class="linha sys">5.3</span></div>
    <p>O <strong>sistema de fábrica, melhorado</strong>. Você continua com tudo o que o aparelho já fazia —
      rádio FM, gravador, vídeo, Bluetooth — e ganha o visual novo, o menu <strong>Aplicativos</strong> com
      os jogos, a <strong>capa do álbum</strong> e o <strong>Atualizar por SD</strong>.</p>
    <p class="detalhe">Para quem quer o player completo, com a cara nova em cima.</p>
  </div>
  <div class="card tipo-sistema">
    <div class="rotulo">Sistema 2</div>
    <h4>OpenPod <strong>RockBox</strong></h4>
    <div class="versoes"><span class="linha rb">5.3.822b9f5e99</span></div>
    <p>O <strong>Rockbox</strong> para o SL6801, com o <strong>visual OpenPod</strong> e o seu idioma. Mais
      formatos de áudio, estável e leve, e uma <strong>loja de apps e jogos</strong> dentro do Tune.</p>
    <p class="detalhe">Para quem quer <strong>música e só</strong>. <em>* Capa do álbum em beta.</em></p>
  </div>
  <div class="card tipo-programa">
    <div class="rotulo">O programa</div>
    <h4>OpenPod <strong>Tune</strong></h4>
    <div class="versoes"><span class="ver">0.4</span></div>
    <p>Não vai para dentro do player: fica no seu <strong>computador</strong>. É ele que instala o System ou o
      RockBox, que atualiza, que guarda a <strong>cópia de segurança</strong> antes de gravar, e que te avisa
      quando há versão nova.</p>
    <p class="detalhe">Grátis, para macOS, Windows e Linux. <a href="#tune">Ver o que ele faz</a>.</p>
  </div>
</div>

<div class="nota"><strong>Dá para trocar de sistema quando quiser.</strong> O Tune refaz a instalação inteira, e as
suas músicas no cartão ficam lá. E, se algo der errado, a <a href="#compat">Recuperação</a> traz o aparelho de
volta ao original.</div>

<p class="sub"><small><span class="linha sys">System 5.3</span> <span class="linha rb">RockBox 5.3</span> <span class="ver">Tune 0.4</span> · 26/11/2026</small></p>'''
    en = f'''<section class="hero">
  <div>
    <h1>OpenPod</h1>
    <p class="sub">A new firmware for music players with the <strong>Smartlink SL6801</strong> chip: a clean look, a focus on music, built on top of the stock system.</p>
    <p class="sub"><small>Tested on the <strong>Ligenai GN-438</strong> and the <strong>GN-408</strong>. <a href="#compat">See compatibility</a></small></p>
    <div class="botoes">
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-macos.dmg">Get Tune for macOS</a>
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-windows.exe">Get Tune for Windows</a>
      <a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/instalador/openpod-tune-linux-x86_64.tar.gz">Get Tune for Linux</a>
      <a class="btn sec" href="#instalar">How to install</a>
    </div>
  </div>
  <figure><img class="tela" alt="OpenPod home screen: top bar with clock, OpenPod and battery; nine dark icons with colored symbols, in a grid, including Apps, the selected one with a white frame" src="{img["home"]}"></figure>
</section>

<h2 id="tipos">What there is</h2>
<p>There are <strong>three things</strong> with different names, and they are easy to mix up. <strong>OpenPod</strong>
is the project. Inside it there are <strong>two systems</strong> for your player, and <strong>one program</strong> that
installs, updates and looks after both.</p>

<div class="tipos">
  <div class="card tipo-sistema">
    <div class="rotulo">System 1</div>
    <h4>OpenPod <strong>System</strong></h4>
    <div class="versoes"><span class="linha sys">5.3</span></div>
    <p>The <strong>stock system, improved</strong>. You keep everything the player already did — FM radio,
      recorder, video, Bluetooth — and gain the new look, the <strong>Apps menu</strong> with the games, the
      <strong>album art</strong> and <strong>Update via SD</strong>.</p>
    <p class="detalhe">For those who want the complete player, with a new face on it.</p>
  </div>
  <div class="card tipo-sistema">
    <div class="rotulo">System 2</div>
    <h4>OpenPod <strong>RockBox</strong></h4>
    <div class="versoes"><span class="linha rb">5.3.822b9f5e99</span></div>
    <p><strong>Rockbox</strong> for the SL6801, with the <strong>OpenPod look</strong> and your language. More
      audio formats, stable and light, and an <strong>app and game store</strong> inside Tune.</p>
    <p class="detalhe">For those who want <strong>music and only that</strong>. <em>* Album art in beta.</em></p>
  </div>
  <div class="card tipo-programa">
    <div class="rotulo">The program</div>
    <h4>OpenPod <strong>Tune</strong></h4>
    <div class="versoes"><span class="ver">0.4</span></div>
    <p>It does not go inside the player: it stays on your <strong>computer</strong>. It is what installs the
      System or the RockBox, updates them, takes the <strong>backup</strong> before writing, and tells you when
      there is a new version.</p>
    <p class="detalhe">Free, for macOS, Windows and Linux. <a href="#tune">See what it does</a>.</p>
  </div>
</div>

<div class="nota"><strong>You can switch systems whenever you want.</strong> Tune redoes the whole install, and the
music on your card stays where it is. And if something goes wrong, <a href="#compat">Recovery</a> brings
the player back to the original.</div>

<p class="sub"><small><span class="linha sys">System 5.3</span> <span class="linha rb">RockBox 5.3</span> <span class="ver">Tune 0.4</span> · 2026-11-26</small></p>'''
    return pt, en


def painel_tune(img):
    pt = f'''<h2 id="tune">O OpenPod Tune</h2>
<p>O Tune é a central de tudo. Ele fala com o player pelo USB, sabe o que é o aparelho, e <strong>só grava o que precisa</strong>.</p>

<div class="grade">
  <div class="card"><h4>Instala</h4><p>Escolhe entre o <strong>System</strong> e o <strong>RockBox</strong>, sempre na versão mais nova. Baixa sozinho, ou você aponta um arquivo.</p></div>
  <div class="card"><h4>Atualiza</h4><p>Duas formas, sempre: pelo <strong>cartão</strong> (sem computador) ou pelo <strong>Recovery</strong> (com o cabo). O Tune decide qual é a certa e te explica.</p></div>
  <div class="card"><h4>Guarda cópia</h4><p>Faz o <strong>backup completo</strong> da flash antes de gravar, no seu computador. É o que traz o aparelho de volta ao original.</p></div>
  <div class="card"><h4>StorePod</h4><p>Uma lojinha de temas, apps e jogos <strong>testados</strong> para o RockBox. Instala e atualiza pelo cartão, sem reinstalar o sistema.</p></div>
</div>

<h3>O que ele confere antes de gravar</h3>
<div class="grade">
  <div class="card"><h4>O aparelho</h4><p>Chip, memória, bateria e a identidade do firmware de fábrica. Aparelho desconhecido: a gravação fica <strong>bloqueada</strong>, e ele te oferece o diagnóstico.</p></div>
  <div class="card"><h4>O pacote</h4><p>Só aceita pacotes <strong>assinados</strong> pelo OpenPod. Cada arquivo tem o seu checksum, dentro da assinatura.</p></div>
  <div class="card"><h4>O que mudou</h4><p>Ele compara a <strong>identidade da flash</strong> (não o número da versão): se é a mesma, <strong>nada</strong> é gravado na flash e o caminho é só o cartão.</p></div>
  <div class="card"><h4>O registro</h4><p>O cartão guarda a versão instalada, com que flash e em que estado. Se uma instalação foi interrompida, ele reconhece e não dá um falso "instalado".</p></div>
</div>

<h3>Cartão ou Recovery?</h3>
<table>
  <tr><td></td><td><strong>Pelo cartão SD</strong></td><td><strong>Pelo Recovery</strong></td></tr>
  <tr><td>Quando serve</td><td>Só a <strong>personalização</strong> mudou (o tema, os idiomas, os plugins)</td><td>O <strong>firmware</strong> mudou (uma versão nova de verdade)</td></tr>
  <tr><td>Precisa de computador</td><td>Não</td><td>Sim, com o cabo</td></tr>
  <tr><td>O que é gravado</td><td>Só a pasta do cartão</td><td>A flash inteira e a pasta do cartão</td></tr>
</table>
<div class="nota">A regra é o <strong>flash_sha256</strong>, não o número da versão. Se o número não subiu mas a flash mudou, o Tune pede o Recovery mesmo assim — é o que evita gravar a coisa errada.</div>

<h3>Dois sistemas, uma escolha</h3>
<div class="sistemas">
<figure class="card"><img class="tela" alt="OpenPod System 5.3: nove ícones e, embaixo, o cartão com o nome da música" src="{img["system"]}">
<figcaption><strong>OpenPod System</strong> · 5.3<br>O sistema de fábrica, melhorado: rádio FM, gravador, vídeo, Bluetooth, jogos e <strong>Atualizar por SD</strong>. Agora com a música que está tocando na tela inicial.</figcaption></figure>
<figure class="card"><img class="tela" alt="OpenPod RockBox: menu com os ícones do OpenPod e o cartão do player" src="{img["rockbox"]}">
<figcaption><strong>OpenPod RockBox</strong> · 5.3<br>O Rockbox para o SL6801, com o <strong>visual OpenPod</strong> e o seu idioma: mais formatos de áudio, estável e leve.<br><small>* Capa do álbum: em beta.</small></figcaption></figure>
</div>
<p>Dá para trocar de um para o outro quando quiser: o Tune refaz a instalação inteira e as suas músicas no cartão continuam lá.</p>

<h3>Instalar em três passos</h3>
<div class="card"><ol class="passos">
  <li>Baixe o Tune (macOS, Windows ou Linux) e abra.</li>
  <li>Escolha o sistema — no RockBox, escolha também o idioma.</li>
  <li>Desligue o player, segure o botão de baixo (play/pause), ligue o cabo, e clique em <strong>Instalar</strong>. Espere a tela <strong>Pronto</strong>, sem tirar o cabo.</li>
</ol>
<p><small><strong>macOS:</strong> na primeira vez, se o macOS bloquear, abra em Ajustes do Sistema → Privacidade e Segurança → "Abrir assim mesmo". O Tune pede a senha do Mac para falar com o player. <strong>Windows:</strong> se aparecer "O Windows protegeu o computador", clique em "Mais informações → Executar assim mesmo". Não precisa instalar driver. <strong>Linux:</strong> descompacte, rode uma vez <code>sh instalar-regra.sh</code> e abra o <code>./openpod-tune</code>.</small></p></div>
<p><small>Problemas? <a href="https://github.com/zeroproj/OpenPod/issues">Abra uma issue</a>.</small></p>'''

    en = f'''<h2 id="tune">OpenPod Tune</h2>
<p>Tune is the centre of everything. It talks to the player over USB, knows what the device is, and <strong>only writes what it has to</strong>.</p>

<div class="grade">
  <div class="card"><h4>Installs</h4><p>Picks between <strong>System</strong> and <strong>RockBox</strong>, always the newest version. It downloads on its own, or you point it at a file.</p></div>
  <div class="card"><h4>Updates</h4><p>Two ways, always: through the <strong>card</strong> (no computer) or through <strong>Recovery</strong> (with the cable). Tune works out which one is right and explains it.</p></div>
  <div class="card"><h4>Keeps a copy</h4><p>Takes a <strong>full backup</strong> of the flash before writing, on your computer. That is what brings the player back to the original.</p></div>
  <div class="card"><h4>StorePod</h4><p>A little shop of themes, apps and <strong>tested</strong> games for RockBox. Installs and updates through the card, without reinstalling the system.</p></div>
</div>

<h3>What it checks before writing</h3>
<div class="grade">
  <div class="card"><h4>The player</h4><p>Chip, memory, battery and the identity of the stock firmware. Unknown player: the write is <strong>blocked</strong>, and it offers you the diagnostic.</p></div>
  <div class="card"><h4>The package</h4><p>Only accepts packages <strong>signed</strong> by OpenPod. Every file has its own checksum, inside the signature.</p></div>
  <div class="card"><h4>What changed</h4><p>It compares the <strong>identity of the flash</strong> (not the version number): if it is the same, <strong>nothing</strong> is written to the flash and the route is the card alone.</p></div>
  <div class="card"><h4>The record</h4><p>The card keeps the installed version, with which flash and in what state. If an install was interrupted, it recognises it and never claims a false "installed".</p></div>
</div>

<h3>Card or Recovery?</h3>
<table>
  <tr><td></td><td><strong>Through the SD card</strong></td><td><strong>Through Recovery</strong></td></tr>
  <tr><td>When it applies</td><td>Only the <strong>customization</strong> changed (the theme, the languages, the plugins)</td><td>The <strong>firmware</strong> changed (a genuinely new version)</td></tr>
  <tr><td>Needs a computer</td><td>No</td><td>Yes, with the cable</td></tr>
  <tr><td>What gets written</td><td>Only the card folder</td><td>The whole flash and the card folder</td></tr>
</table>
<div class="nota">The rule is the <strong>flash_sha256</strong>, not the version number. If the number did not go up but the flash did, Tune asks for Recovery anyway — that is what stops it writing the wrong thing.</div>

<h3>Two systems, one choice</h3>
<div class="sistemas">
<figure class="card"><img class="tela" alt="OpenPod System 5.3: nine icons and, below, the card with the song name" src="{img["system"]}">
<figcaption><strong>OpenPod System</strong> · 5.3<br>The stock system, improved: FM radio, recorder, video, Bluetooth, games and <strong>Update via SD</strong>. Now with the playing song on the home screen.</figcaption></figure>
<figure class="card"><img class="tela" alt="OpenPod RockBox: menu with the OpenPod icons and the player card" src="{img["rockbox"]}">
<figcaption><strong>OpenPod RockBox</strong> · 5.3<br>Rockbox for the SL6801, with the <strong>OpenPod look</strong> and your language: more audio formats, stable and light.<br><small>* Album art: in beta.</small></figcaption></figure>
</div>
<p>You can switch from one to the other whenever you want: Tune redoes the whole install, and the music on your card stays where it is.</p>

<h3>Installing in three steps</h3>
<div class="card"><ol class="passos">
  <li>Download Tune (macOS, Windows or Linux) and open it.</li>
  <li>Pick the system — on RockBox, also pick the language.</li>
  <li>Turn the player off, hold the bottom button (play/pause), plug the cable in, and click <strong>Install</strong>. Wait for the <strong>Done</strong> screen, without unplugging the cable.</li>
</ol>
<p><small><strong>macOS:</strong> the first time, if macOS blocks it, open it in System Settings → Privacy &amp; Security → "Open Anyway". Tune asks for your Mac password to talk to the player. <strong>Windows:</strong> if "Windows protected your PC" shows up, click "More info → Run anyway". No driver to install. <strong>Linux:</strong> unpack it, run <code>sh instalar-regra.sh</code> once, then open <code>./openpod-tune</code>.</small></p></div>
<p><small>Problems? <a href="https://github.com/zeroproj/OpenPod/issues">Open an issue</a>.</small></p>'''
    return pt, en


def painel_recursos():
    pt = '''<h2 id="recursos">Recursos</h2>
<p>Cada linha do OpenPod evolui por conta própria. <strong>OpenPod System</strong>, <strong>OpenPod RockBox</strong>
e <strong>OpenPod Tune</strong> têm as suas próprias melhorias, e as versões saem em dias diferentes.</p>

<div class="linhas">
  <section class="linha-bloco">
    <div class="cabeca"><span class="linha sys">System</span><h3>OpenPod System</h3><span class="ver">5.3</span></div>
    <p class="intro">O firmware que vai na memória do aparelho. É ele que traz as mudanças de visual, os jogos e o <strong>Atualizar por SD</strong>.</p>
    <div class="grade">
      <div class="card"><h4>Visual novo</h4><p>Logo do OpenPod na abertura, fundo preto nas telas, ícones escuros com símbolos coloridos e <strong>moldura branca</strong> no selecionado.</p></div>
      <div class="card"><h4>Na tela inicial</h4><p>Barra superior com relógio, <strong>OpenPod</strong> e bateria. E o nome da música que está tocando, num cartão embaixo dos ícones.</p></div>
      <div class="card"><h4>Capa do álbum</h4><p>Na tela Tocando Agora, lida do próprio MP3. JPEG comum, embutido no arquivo.</p></div>
      <div class="card"><h4>Menu Aplicativos</h4><p>Despertador, Imagem e <strong>jogos</strong> (voar entre obstáculos, encaixar blocos, Cobrinha), com os controles do aparelho.</p></div>
      <div class="card"><h4>Em português</h4><p>Textos revisados: sem "ecrã", sem "ficheiro", sem tradução errada.</p></div>
      <div class="card"><h4>Atualizar por SD</h4><p>As próximas versões entram pelo cartão, sem computador.</p></div>
    </div>
  </section>

  <section class="linha-bloco">
    <div class="cabeca"><span class="linha rb">RockBox</span><h3>OpenPod RockBox</h3><span class="ver">5.3.822b9f5e99</span></div>
    <p class="intro">O Rockbox que vai na memória do aparelho, com a cara do OpenPod. É o que traz os temas, os idiomas e os plugins.</p>
    <div class="grade">
      <div class="card"><h4>Visual OpenPod</h4><p>O tema OpenPod128 e o padrão do Rockbox, em telas de 128×160.</p></div>
      <div class="card"><h4>Volume na tela</h4><p>Ao aumentar ou baixar, a tela Tocando agora mostra a barra e o nível do volume.</p></div>
      <div class="card"><h4>Plugins do próprio sistema</h4><p><strong>Personalizar o menu principal</strong>, <strong>Tempo de reprodução</strong> e <strong>Limpar o disco</strong>.</p></div>
      <div class="card"><h4>Leve e estável</h4><p>Só o que funciona: temas, codecs, idiomas e visualizadores. Os jogos e apps entram testados, aos poucos.</p></div>
      <div class="card"><h4>50 idiomas</h4><p>Com o tema OpenPod traduzido para português.</p></div>
      <div class="card"><h4>Atualiza pelo cartão</h4><p>Quando só a personalização mudou, nem é preciso computador.</p></div>
    </div>
  </section>

  <section class="linha-bloco">
    <div class="cabeca"><span class="linha prog">Tune</span><h3>OpenPod Tune</h3><span class="ver">0.4</span></div>
    <p class="intro">O programa do computador. É ele que instala os dois sistemas, atualiza, guarda as cópias de segurança e avisa quando há coisa nova.</p>
    <div class="grade">
      <div class="card"><h4>Instala os dois</h4><p>Escolhe entre System e RockBox, sempre na versão mais nova, em macOS, Windows e Linux.</p></div>
      <div class="card"><h4>Cópia de segurança</h4><p>Faz o <strong>backup completo</strong> da flash antes de gravar. É o que traz o aparelho de volta ao original.</p></div>
      <div class="card"><h4>StorePod</h4><p>A lojinha de temas, apps e jogos <strong>testados</strong>, que instala pelo cartão sem reinstalar o sistema.</p></div>
      <div class="card"><h4>Escolhe o caminho</h4><p>Cartão ou Recovery: o Tune compara a identidade da flash e diz qual usar.</p></div>
      <div class="card"><h4>Só pacotes assinados</h4><p>Recusa qualquer arquivo que não venha do OpenPod, com a assinatura conferida.</p></div>
      <div class="card"><h4>Diagnóstico</h4><p>Quando o aparelho não é reconhecido, ele recolhe o que precisa e te diz o que fazer.</p></div>
    </div>
  </section>
</div>

<h3>O que o aparelho já fazia (e continua fazendo)</h3>
<ul class="grupo">
  <li><strong>Música</strong>: artistas, álbuns, músicas, pastas e favoritos</li>
  <li>Arquivos de áudio: MP3, AAC/M4A, WMA, FLAC, APE, WAV e OGG</li>
  <li>Letra sincronizada (<code>.lrc</code>) e equalizador</li>
  <li><strong>Vídeo</strong> em AVI (veja abaixo)</li>
  <li><strong>Imagens</strong> em JPEG</li>
  <li><strong>Livro digital</strong> (<code>.txt</code>)</li>
  <li><strong>Gravador de voz</strong></li>
  <li><strong>Rádio FM</strong></li>
  <li><strong>Bluetooth</strong> para fones e caixas de som</li>
  <li><strong>Despertador</strong> (agora no menu Aplicativos)</li>
</ul>
<p><small>Capa: JPEG comum (baseline) embutido no MP3. O ideal é <strong>300×300 a 500×500</strong>; até 1000×1000 e 512 KB funciona. Capa maior, JPEG progressivo ou PNG aparecem como um quadrado cinza, e a música toca normal.</small></p>
<p><small>Os jogos e o kit de apps são baseados no <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>, de <strong>Dmitry Brant</strong> (licença MIT). Obrigado, Dmitry!</small></p>

<h3 id="videos">Vídeo: só um formato toca</h3>
<p>O player de vídeo do aparelho só toca um formato bem específico. Arquivos fora destas regras não aparecem ou não abrem:</p>
<table>
  <tr><td>Arquivo</td><td>extensão <code>.avi</code></td></tr>
  <tr><td>Vídeo</td><td>MJPEG (cada quadro é um JPEG)</td></tr>
  <tr><td>Tamanho</td><td><strong>exatamente 128×160</strong> (a tela em pé)</td></tr>
  <tr><td>Áudio</td><td><strong>estéreo</strong> (2 canais), PCM 16 bits</td></tr>
  <tr><td>Blocos</td><td>cada quadro de no máximo 30 KB</td></tr>
</table>
<h4>Como converter</h4>
<p>Com o <a href="https://ffmpeg.org/">ffmpeg</a> (grátis, Windows/macOS/Linux), troque <code>entrada.mp4</code> pelo seu arquivo:</p>
<pre>ffmpeg -i entrada.mp4 -vf "scale=128:160:force_original_aspect_ratio=decrease,pad=128:160:(ow-iw)/2:(oh-ih)/2,fps=20" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -c:a pcm_s16le -ar 44100 -ac 2 saida.avi</pre>
<p>O vídeo fica em pé, com faixas pretas se não for 4:5. Copie o <code>saida.avi</code> para o cartão e abra em <code>Vídeo</code>.</p>
<div class="aviso"><strong>Imagem espelhada?</strong> Em alguns aparelhos desta família o vídeo aparece invertido da esquerda para a direita. Se acontecer no seu, converta de novo trocando <code>fps=20</code> por <code>hflip,fps=20</code>.</div>
<p><small>Dica: se o vídeo engasgar, diminua para <code>fps=15</code> ou aumente a compressão com <code>-q:v 8</code>.</small></p>'''

    en = '''<h2 id="recursos">Features</h2>
<p>Each line of OpenPod moves on its own. <strong>OpenPod System</strong>, <strong>OpenPod RockBox</strong>
and <strong>OpenPod Tune</strong> have their own improvements, and their versions come out on different days.</p>

<div class="linhas">
  <section class="linha-bloco">
    <div class="cabeca"><span class="linha sys">System</span><h3>OpenPod System</h3><span class="ver">5.3</span></div>
    <p class="intro">The firmware that goes into the player's memory. It is what brings the new look, the games and <strong>Update via SD</strong>.</p>
    <div class="grade">
      <div class="card"><h4>A new look</h4><p>OpenPod logo on boot, black background on the screens, dark icons with colored symbols and a <strong>white frame</strong> on the selected one.</p></div>
      <div class="card"><h4>On the home screen</h4><p>Top bar with clock, <strong>OpenPod</strong> and battery. And the name of the playing song, in a card below the icons.</p></div>
      <div class="card"><h4>Album art</h4><p>On the Now Playing screen, read from the MP3 itself. Plain JPEG, embedded in the file.</p></div>
      <div class="card"><h4>Apps menu</h4><p>Alarm, Image and <strong>games</strong> (flying between obstacles, fitting blocks, Snake), with the player's own controls.</p></div>
      <div class="card"><h4>In Portuguese</h4><p>Revised texts: no "ecrã", no "ficheiro", no wrong translations.</p></div>
      <div class="card"><h4>Update via SD</h4><p>New versions arrive through the card, no computer needed.</p></div>
    </div>
  </section>

  <section class="linha-bloco">
    <div class="cabeca"><span class="linha rb">RockBox</span><h3>OpenPod RockBox</h3><span class="ver">5.3.822b9f5e99</span></div>
    <p class="intro">The Rockbox that goes into the player's memory, with the OpenPod look. It is what brings the themes, the languages and the plugins.</p>
    <div class="grade">
      <div class="card"><h4>The OpenPod look</h4><p>The OpenPod128 theme and the Rockbox default, on 128×160 screens.</p></div>
      <div class="card"><h4>Volume on screen</h4><p>When you turn it up or down, the Now Playing screen shows the bar and the volume level.</p></div>
      <div class="card"><h4>The system's own plugins</h4><p><strong>Customize main menu</strong>, <strong>Playing time</strong> and <strong>Disk tidy</strong>.</p></div>
      <div class="card"><h4>Light and stable</h4><p>Only what works: themes, codecs, languages and viewers. Games and apps arrive tested, little by little.</p></div>
      <div class="card"><h4>50 languages</h4><p>With the OpenPod theme translated into Portuguese.</p></div>
      <div class="card"><h4>Updates through the card</h4><p>When only the customization changed, no computer is needed.</p></div>
    </div>
  </section>

  <section class="linha-bloco">
    <div class="cabeca"><span class="linha prog">Tune</span><h3>OpenPod Tune</h3><span class="ver">0.4</span></div>
    <p class="intro">The program on your computer. It is what installs the two systems, updates them, keeps the backups and tells you when there is something new.</p>
    <div class="grade">
      <div class="card"><h4>Installs both</h4><p>Picks between System and RockBox, always the newest version, on macOS, Windows and Linux.</p></div>
      <div class="card"><h4>Backup</h4><p>Takes a <strong>full backup</strong> of the flash before writing. That is what brings the player back to the original.</p></div>
      <div class="card"><h4>StorePod</h4><p>The shop of themes, apps and <strong>tested</strong> games, which installs through the card without reinstalling the system.</p></div>
      <div class="card"><h4>Picks the route</h4><p>Card or Recovery: Tune compares the identity of the flash and says which one to use.</p></div>
      <div class="card"><h4>Signed packages only</h4><p>Refuses any file that did not come from OpenPod, with the signature checked.</p></div>
      <div class="card"><h4>Diagnostic</h4><p>When the player is not recognised, it collects what it needs and tells you what to do.</p></div>
    </div>
  </section>
</div>

<h3>What the player already did (and still does)</h3>
<ul class="grupo">
  <li><strong>Music</strong>: artists, albums, songs, folders and favorites</li>
  <li>Audio files: MP3, AAC/M4A, WMA, FLAC, APE, WAV and OGG</li>
  <li>Synced lyrics (<code>.lrc</code>) and equalizer</li>
  <li><strong>Video</strong> in AVI (see below)</li>
  <li><strong>Images</strong> in JPEG</li>
  <li><strong>E-books</strong> (<code>.txt</code>)</li>
  <li><strong>Voice recorder</strong></li>
  <li><strong>FM radio</strong></li>
  <li><strong>Bluetooth</strong> for headphones and speakers</li>
  <li><strong>Alarm</strong> (now in the Apps menu)</li>
</ul>
<p><small>Album art: plain (baseline) JPEG embedded in the MP3. The ideal is <strong>300×300 to 500×500</strong>; up to 1000×1000 and 512 KB works. Larger art, progressive JPEG or PNG show as a grey square, and the music plays fine.</small></p>
<p><small>The games and the app kit are based on <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>, by <strong>Dmitry Brant</strong> (MIT licence). Thank you, Dmitry!</small></p>

<h3 id="videos">Video: only one format plays</h3>
<p>The player's video player only plays one very specific format. Files outside these rules do not show up or do not open:</p>
<table>
  <tr><td>File</td><td><code>.avi</code> extension</td></tr>
  <tr><td>Video</td><td>MJPEG (each frame is a JPEG)</td></tr>
  <tr><td>Size</td><td><strong>exactly 128×160</strong> (the screen, upright)</td></tr>
  <tr><td>Audio</td><td><strong>stereo</strong> (2 channels), PCM 16 bits</td></tr>
  <tr><td>Blocks</td><td>each frame at most 30 KB</td></tr>
</table>
<h4>How to convert</h4>
<p>With <a href="https://ffmpeg.org/">ffmpeg</a> (free, Windows/macOS/Linux), replace <code>input.mp4</code> with your file:</p>
<pre>ffmpeg -i input.mp4 -vf "scale=128:160:force_original_aspect_ratio=decrease,pad=128:160:(ow-iw)/2:(oh-ih)/2,fps=20" -c:v mjpeg -q:v 5 -pix_fmt yuvj420p -c:a pcm_s16le -ar 44100 -ac 2 output.avi</pre>
<p>The video stays upright, with black bars if it is not 4:5. Copy <code>output.avi</code> to the card and open it in <code>Video</code>.</p>
<div class="aviso"><strong>Mirrored picture?</strong> On some players of this family the video shows upside down from left to right. If that happens to you, convert again with <code>fps=20</code> replaced by <code>hflip,fps=20</code>.</div>
<p><small>Tip: if the video stutters, drop to <code>fps=15</code> or raise the compression with <code>-q:v 8</code>.</small></p>'''
    return pt, en


def painel_compat():
    pt = '''<h2 id="compat">Compatibilidade</h2>
<p>O OpenPod funciona em players com o chip <strong>Smartlink SL6801</strong> e o firmware de fábrica <strong>yp3_2.0.43</strong> (aparece nas configurações do aparelho).</p>
<table>
  <tr><td>Chip</td><td>Smartlink <strong>SL6801</strong>, memória de 2 MB. No modo de gravação, o Flashloader mostra <code>chip name: sl6801</code>.</td></tr>
  <tr><td>Firmware</td><td><strong>yp3_2.0.43</strong></td></tr>
  <tr><td>Ligenai GN-438</td><td><span class="ok">Testado</span>: é o aparelho em que o OpenPod é feito.</td></tr>
  <tr><td>GN-408</td><td><span class="ok">Testado por usuários</span>: mesmo chip e firmware; a 2.2.1 funciona.</td></tr>
  <tr><td>Outros SL6801</td><td>Não testados. Se tiver o mesmo chip e o mesmo firmware, é provável que funcione, mas o risco é seu.</td></tr>
</table>
<div class="aviso"><strong>Em aparelho que não é o GN-438, faça um backup antes.</strong> O Tune faz isso sozinho antes de gravar, mas vale ter uma cópia: com o <a href="https://github.com/ilyakurdyukov/smartlink_flash">smartlink_flash</a> (Linux/macOS): <code>sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M meu_backup.bin</code>. Guarde o arquivo: só o backup do <strong>seu</strong> aparelho serve para voltar ao original dele.</div>

<h3>Recuperar o aparelho</h3>
<p>Quer voltar ao sistema original? Há duas opções. As duas usam o firmware de fábrica do <strong>Ligenai GN-438</strong> (<code>yp3_2.0.43</code>).</p>
<table>
  <tr><td></td><td><strong>OpenPod Recovery System (ORS)</strong></td><td><strong>Factory Reset (FR)</strong></td></tr>
  <tr><td>O que é</td><td>O firmware de fábrica com <strong>uma única mudança</strong>: o item <code>Atualizar por SD</code></td><td>O firmware de fábrica <strong>idêntico</strong>, byte a byte</td></tr>
  <tr><td>Visual e funções</td><td>Os originais</td><td>Os originais</td></tr>
  <tr><td>Voltar ao OpenPod depois</td><td>✅ <strong>Só com o cartão SD</strong></td><td>⚠️ Precisa do <strong>computador</strong> de novo</td></tr>
  <tr><td>Indicado para</td><td>Quem quer o original, mas talvez volte ao OpenPod</td><td>Quem quer apagar qualquer vestígio do OpenPod</td></tr>
</table>
<div class="aviso"><strong>Recomendamos o ORS.</strong> Ele deixa o aparelho como o original e não fecha a porta: para voltar ao OpenPod, basta o cartão.</div>
<div class="card"><h4>OpenPod Recovery System (recomendado)</h4>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/recovery/ors/update.up">Baixar o ORS (update.up)</a></div>
<ol class="passos">
  <li><strong>Se o aparelho está com o OpenPod:</strong> copie o <code>update.up</code> para a <strong>raiz</strong> do cartão, vá em <code>Config → Atualizar por SD → Sim</code> e apague o <code>update.up</code> depois.</li>
  <li><strong>Se o aparelho não liga ou não tem o OpenPod:</strong> use o <a href="#legacy">método antigo</a> (primeira instalação pelo computador), escolhendo este arquivo no gravador.</li>
  <li><strong>Para voltar ao OpenPod depois:</strong> baixe a versão mais recente, copie como <code>update.up</code> e use <code>Config → Atualizar por SD</code>.</li>
</ol></div>
<div class="card"><h4>Factory Reset</h4>
<div class="botoes"><a class="btn sec" href="https://github.com/zeroproj/OpenPod/raw/main/recovery/fr/update.up">Baixar o Factory Reset (update.up)</a></div>
<ol class="passos">
  <li><strong>Pelo OpenPod:</strong> copie o <code>update.up</code> para a raiz do cartão e use <code>Config → Atualizar por SD → Sim</code>.</li>
  <li><strong>Pelo computador:</strong> como na primeira instalação, escolhendo este arquivo.</li>
  <li>Depois disso, o aparelho <strong>não tem mais</strong> <code>Atualizar por SD</code>: voltar ao OpenPod só pelo computador.</li>
</ol></div>
<div class="aviso"><strong>Outro modelo?</strong> Os dois arquivos são do <strong>GN-438</strong>. Em qualquer outro aparelho, restaure o <strong>seu próprio backup</strong>.</div>'''

    en = '''<h2 id="compat">Compatibility</h2>
<p>OpenPod works on players with the <strong>Smartlink SL6801</strong> chip and the stock firmware <strong>yp3_2.0.43</strong> (it shows up in the player's settings).</p>
<table>
  <tr><td>Chip</td><td>Smartlink <strong>SL6801</strong>, 2 MB of memory. In write mode, the Flashloader shows <code>chip name: sl6801</code>.</td></tr>
  <tr><td>Firmware</td><td><strong>yp3_2.0.43</strong></td></tr>
  <tr><td>Ligenai GN-438</td><td><span class="ok">Tested</span>: it is the player OpenPod is made on.</td></tr>
  <tr><td>GN-408</td><td><span class="ok">Tested by users</span>: same chip and firmware; 2.2.1 works.</td></tr>
  <tr><td>Other SL6801</td><td>Not tested. Same chip and same firmware means it will probably work, but the risk is yours.</td></tr>
</table>
<div class="aviso"><strong>On a player that is not the GN-438, take a backup first.</strong> Tune does that on its own before writing, but it is worth having a copy: with <a href="https://github.com/ilyakurdyukov/smartlink_flash">smartlink_flash</a> (Linux/macOS): <code>sudo ./smtlink_dump --id 301a:2801 flash_id read_flash 0 2M my_backup.bin</code>. Keep the file: only <strong>your own</strong> player's backup brings your player back to its original.</div>

<h3>Recovering the player</h3>
<p>Want to go back to the original system? There are two options. Both use the stock firmware of the <strong>Ligenai GN-438</strong> (<code>yp3_2.0.43</code>).</p>
<table>
  <tr><td></td><td><strong>OpenPod Recovery System (ORS)</strong></td><td><strong>Factory Reset (FR)</strong></td></tr>
  <tr><td>What it is</td><td>The stock firmware with <strong>one single change</strong>: the <code>Update via SD</code> item</td><td>The stock firmware <strong>identical</strong>, byte for byte</td></tr>
  <tr><td>Look and features</td><td>The originals</td><td>The originals</td></tr>
  <tr><td>Back to OpenPod later</td><td>✅ <strong>With the SD card only</strong></td><td>⚠️ Needs the <strong>computer</strong> again</td></tr>
  <tr><td>Best for</td><td>Those who want the original but may come back to OpenPod</td><td>Those who want to erase every trace of OpenPod</td></tr>
</table>
<div class="aviso"><strong>We recommend ORS.</strong> It leaves the player as the original and does not close the door: to come back to OpenPod, the card is enough.</div>
<div class="card"><h4>OpenPod Recovery System (recommended)</h4>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/recovery/ors/update.up">Download ORS (update.up)</a></div>
<ol class="passos">
  <li><strong>If the player has OpenPod:</strong> copy <code>update.up</code> to the <strong>root</strong> of the card, go to <code>Config → Update via SD → Yes</code>, and delete <code>update.up</code> afterwards.</li>
  <li><strong>If the player does not boot or has no OpenPod:</strong> use the <a href="#legacy">old method</a> (first install over the computer), choosing this file in the writer.</li>
  <li><strong>To come back to OpenPod later:</strong> download the newest version, copy it as <code>update.up</code> and use <code>Config → Update via SD</code>.</li>
</ol></div>
<div class="card"><h4>Factory Reset</h4>
<div class="botoes"><a class="btn sec" href="https://github.com/zeroproj/OpenPod/raw/main/recovery/fr/update.up">Download Factory Reset (update.up)</a></div>
<ol class="passos">
  <li><strong>Through OpenPod:</strong> copy <code>update.up</code> to the card root and use <code>Config → Update via SD → Yes</code>.</li>
  <li><strong>Through the computer:</strong> as in the first install, choosing this file.</li>
  <li>After that, the player <strong>no longer has</strong> <code>Update via SD</code>: back to OpenPod only through the computer.</li>
</ol></div>
<div class="aviso"><strong>Another model?</strong> Both files are for the <strong>GN-438</strong>. On any other player, restore <strong>your own backup</strong>.</div>'''
    return pt, en


def painel_legacy():
    """Os METODOS ANTIGOS: gravador da Shenju e update.up na mao."""
    pt = '''<div class="painel-legacy">
<div class="aviso-legacy"><strong>Esta página é o método antigo.</strong> Ele funciona, e continua sendo a saída quando o OpenPod Tune não dá conta (por exemplo, um aparelho que nem liga). Mas é mais longo e mais fácil de errar. <strong>Se você está começando, use o <a href="#tune">OpenPod Tune</a>.</strong></div>

<h2>Método antigo: gravar com o gravador do fabricante</h2>
<p>É o caminho que existia antes do Tune. Precisa de um <strong>computador com Windows</strong>, do cabo USB e do programa oficial do fabricante do chip (o <strong>Flashloader SL-DEV</strong>, que é da Shenju — não é do OpenPod).</p>

<div class="card"><h4>1. Baixe os dois arquivos</h4>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/atual/update.up">OpenPod — versão mais recente (update.up)</a><a class="btn sec" href="https://github.com/zeroproj/OpenPod/raw/main/atual/FlashloaderSL-DEV-6.9.5.exe">Gravador Flashloader 6.9.5 (.exe)</a></div>
<p><small>O gravador é o programa oficial da Shenju, fabricante do chip do aparelho. Não é do OpenPod.</small></p></div>

<div class="card"><h4>2. Abra o gravador e deixe em inglês</h4>
<p>Abra o <code>FlashloaderSL-DEV-6.9.5.exe</code>. Ele abre em chinês. No menu, vá em <code>setting → Language → English</code>.</p></div>

<div class="card"><h4>3. Configure (uma vez só)</h4>
<p>No menu, vá em <code>setting → Develp setting...</code>. Essa janela continua em chinês, então siga pela posição das caixas:</p>
<table>
  <tr><td>✅ Marque</td><td><strong>as três primeiras</strong> caixas:<br>1. 自动下载 — gravar automático<br>2. 烧录完后自动重启 — reiniciar depois de gravar<br>3. 烧录完重启后恢复出厂设置 — voltar ao padrão ao reiniciar</td></tr>
  <tr><td>⛔ Não marque</td><td>4. 仅擦除 — só apagar<br>6. 频偏校准 — apaga dados de calibração</td></tr>
  <tr><td>✋ Não mexa</td><td>no tamanho da flash e nos campos de endereço Bluetooth</td></tr>
</table>
<p>Clique em <code>Save</code>.</p></div>

<div class="card"><h4>4. Escolha o arquivo do OpenPod</h4>
<p>Clique em <code>Select .up file</code> (canto superior direito) e escolha o <code>update.up</code> que você baixou. Confira se o caminho mostrado termina em <code>update.up</code>.</p></div>

<div class="card"><h4>5. Coloque o aparelho no modo de gravação</h4>
<p>Conecte o player ao computador pelo cabo USB.</p>
<ol type="a">
  <li>Com um <strong>clipe de papel desdobrado</strong> (ou outro objeto fino e adequado), pressione suavemente o botão <strong>RESET</strong>, no pequeno orifício na lateral do aparelho.</li>
  <li>Pressione e mantenha pressionado o botão <strong>VOL para baixo</strong> (diminuir volume).</li>
  <li>Enquanto mantém o volume pressionado, retire o clipe do botão RESET.</li>
  <li><strong>Continue segurando o volume para baixo por uns 3 segundos.</strong></li>
</ol>
<p>A tela do aparelho fica <strong>preta</strong> e o computador reconhece o aparelho em modo de gravação.</p>
<p>A tela do aparelho fica <strong>apagada</strong> — é assim mesmo. Se o Windows perguntar se quer <strong>formatar</strong>, responda <strong>não</strong> e feche a janela.</p>
<p><strong>O botão <code>Burn</code> não ficou clicável?</strong> Tente nesta ordem (dica de um usuário do GN-408):</p>
<ol type="a">
  <li>Feche o gravador e tire o cabo USB. Deixe o aparelho desligado.</li>
  <li><strong>Segure</strong> o <strong>volume para baixo</strong> e não solte.</li>
  <li>Ainda segurando, aperte e solte o <strong>RESET</strong>.</li>
  <li>Ainda segurando o volume, <strong>conecte o cabo</strong> no computador.</li>
  <li>Espere <strong>3 segundos</strong> e solte o volume.</li>
  <li>Abra o gravador: ele deve mostrar o aparelho conectado e o <code>Burn</code> fica clicável.</li>
</ol></div>

<div class="card"><h4>6. Grave</h4>
<p>Clique em <code>Burn</code> e espere a barra chegar a <strong>100%</strong>. <strong>Não desconecte nada</strong> enquanto grava. No fim, o aparelho reinicia sozinho.</p></div>

<div class="card"><h4>7. Confira</h4>
<p>No aparelho, abra <code>Config → Informações</code>. Tem que aparecer a versão do OpenPod (começa com <code>OpenPod</code>). Pronto!</p></div>

<h2>Método antigo: atualizar pelo cartão, na mão</h2>
<p>Quando a flash não muda (só a personalização), dá para atualizar sem o Tune e sem computador:</p>
<div class="card"><ol class="passos">
  <li>Baixe a versão mais recente (o botão no topo da página). O arquivo já vem com o nome certo: <code>update.up</code>.</li>
  <li>Copie o <code>update.up</code> para a <strong>raiz</strong> do cartão (fora de qualquer pasta).</li>
  <li>Coloque o cartão no aparelho e vá em <code>Config → Atualizar por SD → Sim</code>.</li>
  <li>O aparelho reinicia, atualiza e volta sozinho.</li>
  <li><strong>Apague o <code>update.up</code> do cartão.</strong> Se ficar lá, ele tenta atualizar toda vez que liga.</li>
</ol></div>

<h2>Quando usar o método antigo</h2>
<table>
  <tr><td>Situação</td><td>O que fazer</td></tr>
  <tr><td>O Tune não instala</td><td>Use o gravador (primeira instalação) e <strong>reporte no GitHub</strong> — o Tune é o caminho que queremos que funcione.</td></tr>
  <tr><td>O aparelho nem liga</td><td>Use o gravador: o modo de gravação fica na memória do chip e funciona mesmo sem o sistema.</td></tr>
  <tr><td>Só a personalização mudou</td><td>O caminho do cartão, à mão, resolve.</td></tr>
  <tr><td>Quer o firmware de fábrica</td><td>Baixe o ORS ou o Factory Reset na seção <a href="#compat">Compatibilidade</a> e instale pelo gravador.</td></tr>
</table>
<div class="aviso-legacy">Este método grava sem fazer a conferência que o Tune faz: ele não confere o aparelho, não confere o pacote e não guarda uma cópia de segurança. <strong>Faça um backup antes</strong> (veja <a href="#compat">Compatibilidade</a>).</div>
</div>'''

    en = '''<div class="painel-legacy">
<div class="aviso-legacy"><strong>This page is the old method.</strong> It works, and it is still the way out when OpenPod Tune cannot do it (a player that does not even boot, for example). But it is longer and easier to get wrong. <strong>If you are starting out, use <a href="#tune">OpenPod Tune</a>.</strong></div>

<h2>Old method: writing with the manufacturer's writer</h2>
<p>This is the way there was before Tune. It needs a <strong>computer with Windows</strong>, the USB cable, and the chip maker's own program (the <strong>Flashloader SL-DEV</strong>, from Shenju — it is not from OpenPod).</p>

<div class="card"><h4>1. Download the two files</h4>
<div class="botoes"><a class="btn" href="https://github.com/zeroproj/OpenPod/raw/main/atual/update.up">OpenPod — newest version (update.up)</a><a class="btn sec" href="https://github.com/zeroproj/OpenPod/raw/main/atual/FlashloaderSL-DEV-6.9.5.exe">Flashloader 6.9.5 writer (.exe)</a></div>
<p><small>The writer is the official program from Shenju, the chip maker. It is not from OpenPod.</small></p></div>

<div class="card"><h4>2. Open the writer and set it to English</h4>
<p>Open <code>FlashloaderSL-DEV-6.9.5.exe</code>. It opens in Chinese. In the menu, go to <code>setting → Language → English</code>.</p></div>

<div class="card"><h4>3. Configure it (once)</h4>
<p>In the menu, go to <code>setting → Develp setting...</code>. This window stays in Chinese, so follow the position of the boxes:</p>
<table>
  <tr><td>✅ Tick</td><td><strong>the first three</strong> boxes:<br>1. 自动下载 — automatic write<br>2. 烧录完后自动重启 — restart after writing<br>3. 烧录完重启后恢复出厂设置 — back to defaults on restart</td></tr>
  <tr><td>⛔ Do not tick</td><td>4. 仅擦除 — erase only<br>6. 频偏校准 — erases calibration data</td></tr>
  <tr><td>✋ Leave alone</td><td>the flash size and the Bluetooth address fields</td></tr>
</table>
<p>Click <code>Save</code>.</p></div>

<div class="card"><h4>4. Choose the OpenPod file</h4>
<p>Click <code>Select .up file</code> (top right) and choose the <code>update.up</code> you downloaded. Check that the path shown ends with <code>update.up</code>.</p></div>

<div class="card"><h4>5. Put the player in write mode</h4>
<p>Connect the player to the computer with the USB cable.</p>
<ol type="a">
  <li>With an <strong>unfolded paper clip</strong> (or another thin, suitable object), press the <strong>RESET</strong> button gently, in the small hole on the side of the player.</li>
  <li>Press and hold the <strong>VOL down</strong> button (volume down).</li>
  <li>While holding the volume down, pull the clip out of the RESET button.</li>
  <li><strong>Keep holding volume down for about 3 seconds.</strong></li>
</ol>
<p>The player's screen stays <strong>black</strong> and the computer recognises the player in write mode.</p>
<p>The player's screen stays <strong>blank</strong> — that is normal. If Windows asks whether it wants to <strong>format</strong>, answer <strong>no</strong> and close the window.</p>
<p><strong>The <code>Burn</code> button is not clickable?</strong> Try in this order (a tip from a GN-408 user):</p>
<ol type="a">
  <li>Close the writer and unplug the cable. Leave the player off.</li>
  <li><strong>Hold</strong> <strong>volume down</strong> and do not let go.</li>
  <li>Still holding, press and release <strong>RESET</strong>.</li>
  <li>Still holding the volume, <strong>plug the cable</strong> into the computer.</li>
  <li>Wait <strong>3 seconds</strong> and release the volume.</li>
  <li>Open the writer: it should show the player connected and <code>Burn</code> becomes clickable.</li>
</ol></div>

<div class="card"><h4>6. Write</h4>
<p>Click <code>Burn</code> and wait for the bar to reach <strong>100%</strong>. <strong>Do not unplug anything</strong> while it writes. When it finishes, the player restarts on its own.</p></div>

<div class="card"><h4>7. Check</h4>
<p>On the player, open <code>Config → Information</code>. The OpenPod version must show up (it starts with <code>OpenPod</code>). Done!</p></div>

<h2>Old method: updating through the card, by hand</h2>
<p>When the flash does not change (only the customization), you can update without Tune and without a computer:</p>
<div class="card"><ol class="passos">
  <li>Download the newest version (the button at the top of the page). The file already has the right name: <code>update.up</code>.</li>
  <li>Copy <code>update.up</code> to the <strong>root</strong> of the card (not inside any folder).</li>
  <li>Put the card in the player and go to <code>Config → Update via SD → Yes</code>.</li>
  <li>The player restarts, updates and comes back on its own.</li>
  <li><strong>Delete <code>update.up</code> from the card.</strong> If it stays, it tries to update every time it turns on.</li>
</ol></div>

<h2>When to use the old method</h2>
<table>
  <tr><td>Situation</td><td>What to do</td></tr>
  <tr><td>Tune will not install</td><td>Use the writer (first install) and <strong>report it on GitHub</strong> — Tune is the way we want to work.</td></tr>
  <tr><td>The player does not even boot</td><td>Use the writer: write mode lives in the chip's own memory and works even without the system.</td></tr>
  <tr><td>Only the customization changed</td><td>The card route, by hand, does it.</td></tr>
  <tr><td>You want the stock firmware</td><td>Download ORS or Factory Reset from the <a href="#compat">Compatibility</a> section and install with the writer.</td></tr>
</table>
<div class="aviso-legacy">This method writes without the checks Tune makes: it does not check the player, does not check the package and does not keep a backup. <strong>Take a backup first</strong> (see <a href="#compat">Compatibility</a>).</div>
</div>'''
    return pt, en


def painel_sobre():
    pt = '''<h2 id="sobre">Sobre o OpenPod</h2>
<p>O OpenPod é um firmware novo para players de música baratos com o chip <strong>Smartlink SL6801</strong>, começando pelo <strong>Ligenai GN-438</strong>. A ideia é transformar um aparelho simples num player dedicado à música, com visual limpo e navegação rápida.</p>
<div class="card"><p><strong>A filosofia:</strong> usar o que o aparelho já faz bem e melhorar antes de substituir. O OpenPod não é um sistema escrito do zero: ele parte do firmware de fábrica (<code>yp3_2.0.43</code>), estudado por engenharia reversa, e muda aos poucos o que precisa mudar. Cada versão é testada no aparelho antes de sair.</p></div>

<h3>Suporte</h3>
<p>Encontrou um problema ou tem uma dúvida? <a href="https://github.com/zeroproj/OpenPod/issues">Abra uma issue no GitHub</a>. Conte o modelo do player, o sistema (OpenPod System ou RockBox) e o que aconteceu.</p>

<h3>Créditos e agradecimentos</h3>
<table>
  <tr><td><strong>Jayden Milne</strong><br><a href="https://github.com/jaydens-tasty-slop/rockbox">Rockbox YP3</a> · <a href="https://github.com/jaydens-tasty-slop/rockslop">rockslop</a></td><td>O <strong>OpenPod RockBox nasceu do trabalho dele</strong>: o port do Rockbox para o SL6801 foi a nossa base, e a partir dele seguimos como um projeto próprio, com visual, instalador e caminhos nossos. Do rockslop vem a parte do <strong>OpenPod Tune</strong> que fala com o player pelo USB. Licença GPL.</td></tr>
  <tr><td><strong>Projeto Rockbox</strong><br><a href="https://www.rockbox.org/">rockbox.org</a></td><td>O firmware livre de players de música, com codecs, plugins, temas e idiomas. Licença GPL.</td></tr>
  <tr><td><strong>Yury Pliashkou</strong><br><a href="https://github.com/pliashkou/epet">ePet</a></td><td>As regras do bichinho virtual previsto para a 5.4. Licença MIT.</td></tr>
  <tr><td><strong>Rasmus Andersson</strong><br><a href="https://rsms.me/inter/">Inter</a></td><td>A fonte do tema OpenPod do RockBox e do Tune. Licença SIL OFL 1.1.</td></tr>
  <tr><td><strong>Dmitry Brant</strong><br><a href="https://github.com/dbrant/SL6801_player">SL6801_player</a></td><td>O kit de desenvolvimento de apps para o SL6801, com jogos e um mapa detalhado do chip. Os <strong>jogos e o kit de apps</strong> do menu Aplicativos são baseados no trabalho dele, sob a <strong>licença MIT</strong>, com a permissão e a confirmação do autor. Também foi dele a confirmação de que o som não pode rodar na tarefa da tela. Obrigado, Dmitry!</td></tr>
  <tr><td><strong>Ilya Kurdyukov</strong><br><a href="https://github.com/ilyakurdyukov/smartlink_flash">smartlink_flash</a></td><td>A ferramenta que lê e grava a memória flash desses chips pelo USB, no Linux e no macOS. Foi com ela que tiramos o backup original do GN-438 e que o Tune grava o OpenPod.</td></tr>
  <tr><td><strong>Comunidade do Reddit</strong></td><td>Quem testou no <strong>GN-408</strong> e ajustou o passo a passo da instalação, quem reportou travamentos e quem testou capas de tamanhos diferentes. Cada relato virou correção.</td></tr>
</table>
<p><small>Guardamos uma cópia (fork) de cada projeto que usamos, na conta <a href="https://github.com/zeroproj">zeroproj</a>, para preservar a versão exata. A lista completa está em <a href="https://github.com/zeroproj/OpenPod/blob/main/REFERENCIAS.md">REFERENCIAS.md</a>.</small></p>

<h3>No que nos inspiramos</h3>
<ul>
  <li><strong><a href="https://www.rockbox.org/">Rockbox</a></strong>: o firmware livre que deu vida nova a tantos players. Dele vêm as ideias de apps no aparelho, de um caminho seguro de volta ao original e de instruções claras. O Rockbox em si não cabe neste chip (são cerca de 512 KB de RAM), então o OpenPod segue o caminho possível: melhorar o firmware de fábrica.</li>
  <li><strong>Os players de música dedicados clássicos</strong>: menus simples, poucas informações por tela, seleção clara e foco total na música.</li>
</ul>

<h3>Por dentro do aparelho</h3>
<p>O firmware de fábrica usa componentes de código aberto, que o OpenPod mantém e aproveita: <strong><a href="https://lvgl.io/">LVGL</a></strong> (a interface gráfica), <strong><a href="https://www.freertos.org/">FreeRTOS</a></strong> (o sistema que divide as tarefas) e o <strong><a href="http://elm-chan.org/fsw/tjpgd/">TJpgDec</a></strong>, de ChaN (o decodificador de JPEG que desenha a capa do álbum). Para gravar pelo Windows, usamos o <strong>Flashloader SL-DEV</strong>, a ferramenta oficial do fabricante do chip.</p>

<h3>Código-fonte e engenharia reversa</h3>
<div class="card"><p><strong>Quer estudar o chip ou programar para ele?</strong> Vá ao projeto do Dmitry, o <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>. Ele é <strong>aberto</strong> (licença MIT) e traz o kit de desenvolvimento, jogos de exemplo, o mapa do chip e as ferramentas de engenharia reversa dele. É o melhor ponto de partida para quem quer criar algo para o SL6801.</p>
<p>A engenharia reversa do OpenPod é <strong>independente</strong>: feita por nós, a partir do firmware de fábrica do GN-438. Ela <strong>não é pública</strong>, e o código-fonte do OpenPod também não. Aqui distribuímos só os arquivos prontos para instalar.</p></div>

<h3>Código aberto do lado RockBox</h3>
<div class="card"><p><strong>O lado RockBox é aberto (GPL).</strong> O código do <a href="https://github.com/zeroproj/openpod-installer">OpenPod Tune</a> e o do <a href="https://github.com/zeroproj/rockbox-gn438">Rockbox que distribuímos</a> estão públicos, como a licença GPL pede. O código do OpenPod System continua fechado.</p></div>

<h3>Licenças</h3>
<ul>
  <li>O código do <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a> vem sob a licença MIT. O texto completo da licença vai no <code>README.md</code> de cada pacote.</li>
  <li>O <strong>Rockbox</strong>, o rockslop e o <strong>OpenPod Tune</strong> são <strong>GPL</strong> (código-fonte nos links acima). A fonte <strong>Inter</strong> é SIL OFL 1.1.</li>
  <li>O <strong>Flashloader SL-DEV</strong> é proprietário e é distribuído no pacote só para gravar o aparelho.</li>
</ul>
<div class="aviso">O OpenPod é um projeto <strong>independente</strong>, sem ligação com a Smartlink, a Shenju, a Ligenai ou qualquer fabricante. Os nomes citados pertencem aos seus donos.</div>'''

    en = '''<h2 id="about">About OpenPod</h2>
<p>OpenPod is a new firmware for cheap music players with the <strong>Smartlink SL6801</strong> chip, starting with the <strong>Ligenai GN-438</strong>. The idea is to turn a simple device into a player dedicated to music, with a clean look and quick navigation.</p>
<div class="card"><p><strong>The philosophy:</strong> use what the player already does well and improve before replacing. OpenPod is not a system written from scratch: it starts from the stock firmware (<code>yp3_2.0.43</code>), studied by reverse engineering, and changes, little by little, what needs changing. Every version is tested on the device before it ships.</p></div>

<h3>Support</h3>
<p>Found a problem or have a question? <a href="https://github.com/zeroproj/OpenPod/issues">Open an issue on GitHub</a>. Say the player model, the system (OpenPod System or RockBox) and what happened.</p>

<h3>Credits and thanks</h3>
<table>
  <tr><td><strong>Jayden Milne</strong><br><a href="https://github.com/jaydens-tasty-slop/rockbox">Rockbox YP3</a> · <a href="https://github.com/jaydens-tasty-slop/rockslop">rockslop</a></td><td><strong>OpenPod RockBox was born from his work</strong>: the Rockbox port to the SL6801 was our base, and from there we carry on as a project of our own, with our own look, installer and paths. From rockslop comes the part of <strong>OpenPod Tune</strong> that talks to the player over USB. GPL licence.</td></tr>
  <tr><td><strong>The Rockbox project</strong><br><a href="https://www.rockbox.org/">rockbox.org</a></td><td>The free firmware for music players, with codecs, plugins, themes and languages. GPL licence.</td></tr>
  <tr><td><strong>Yury Pliashkou</strong><br><a href="https://github.com/pliashkou/epet">ePet</a></td><td>The rules of the virtual pet planned for 5.4. MIT licence.</td></tr>
  <tr><td><strong>Rasmus Andersson</strong><br><a href="https://rsms.me/inter/">Inter</a></td><td>The typeface of the OpenPod RockBox theme and of Tune. SIL OFL 1.1 licence.</td></tr>
  <tr><td><strong>Dmitry Brant</strong><br><a href="https://github.com/dbrant/SL6801_player">SL6801_player</a></td><td>The app development kit for the SL6801, with games and a detailed map of the chip. The <strong>games and the app kit</strong> in the Apps menu are based on his work, under the <strong>MIT licence</strong>, with the author's permission and confirmation. It was also his confirmation that sound must not run in the UI task. Thank you, Dmitry!</td></tr>
  <tr><td><strong>Ilya Kurdyukov</strong><br><a href="https://github.com/ilyakurdyukov/smartlink_flash">smartlink_flash</a></td><td>The tool that reads and writes the flash memory of these chips over USB, on Linux and macOS. It was with it that we took the original backup of the GN-438, and that Tune writes OpenPod.</td></tr>
  <tr><td><strong>The Reddit community</strong></td><td>Those who tested on the <strong>GN-408</strong> and fixed the install steps, those who reported freezes and those who tried covers of different sizes. Every report became a fix.</td></tr>
</table>
<p><small>We keep a copy (fork) of every project we use, in the <a href="https://github.com/zeroproj">zeroproj</a> account, to preserve the exact version. The full list is in <a href="https://github.com/zeroproj/OpenPod/blob/main/REFERENCIAS.md">REFERENCIAS.md</a>.</small></p>

<h3>What inspired us</h3>
<ul>
  <li><strong><a href="https://www.rockbox.org/">Rockbox</a></strong>: the free firmware that gave new life to so many players. From it come the ideas of apps on the device, of a safe way back to the original and of clear instructions. Rockbox itself does not fit in this chip (it has about 512 KB of RAM), so OpenPod takes the possible route: improving the stock firmware.</li>
  <li><strong>The classic dedicated music players</strong>: simple menus, little information per screen, clear selection and a total focus on the music.</li>
</ul>

<h3>Inside the player</h3>
<p>The stock firmware uses open source components that OpenPod keeps and builds on: <strong><a href="https://lvgl.io/">LVGL</a></strong> (the graphical interface), <strong><a href="https://www.freertos.org/">FreeRTOS</a></strong> (the system that splits the tasks) and <strong><a href="http://elm-chan.org/fsw/tjpgd/">TJpgDec</a></strong>, by ChaN (the JPEG decoder that draws the album art). To write on Windows we use the <strong>Flashloader SL-DEV</strong>, the chip maker's own tool.</p>

<h3>Source code and reverse engineering</h3>
<div class="card"><p><strong>Want to study the chip or program for it?</strong> Go to Dmitry's project, <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>. It is <strong>open</strong> (MIT licence) and brings the development kit, sample games, the chip map and his reverse engineering tools. It is the best starting point for anyone who wants to make something for the SL6801.</p>
<p>OpenPod's reverse engineering is <strong>independent</strong>: done by us, from the GN-438's stock firmware. It is <strong>not public</strong>, and neither is OpenPod's source code. Here we only ship the ready-to-install files.</p></div>

<h3>Open source on the RockBox side</h3>
<div class="card"><p><strong>The RockBox side is open (GPL).</strong> The code of <a href="https://github.com/zeroproj/openpod-installer">OpenPod Tune</a> and of the <a href="https://github.com/zeroproj/rockbox-gn438">Rockbox we ship</a> are public, as the GPL requires. OpenPod System's source code stays closed.</p></div>

<h3>Licences</h3>
<ul>
  <li>The code of <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a> comes under the MIT licence. The full text of the licence ships in each package's <code>README.md</code>.</li>
  <li><strong>Rockbox</strong>, rockslop and <strong>OpenPod Tune</strong> are <strong>GPL</strong> (source code at the links above). The <strong>Inter</strong> typeface is SIL OFL 1.1.</li>
  <li>The <strong>Flashloader SL-DEV</strong> is proprietary and is shipped in the package only to write to the player.</li>
</ul>
<div class="aviso">OpenPod is an <strong>independent</strong> project, with no connection to Smartlink, Shenju, Ligenai or any manufacturer. The names mentioned belong to their owners.</div>'''
    return pt, en


def painel_historico():
    pt = '''<h2 id="historico">Histórico</h2>
<h3>OpenPod System</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">5.3 · 26/11/2026</div><div class="titulo">Renumeração da 3.5</div><div class="texto">Mesmas funções, nome novo: o System passa a 5.x, para ficar lado a lado com o RockBox 5.x.</div></div>
  <div class="item"><div class="quando">3.5 · 22/11/2026</div><div class="titulo">Player na tela inicial</div><div class="texto">O nome da música que está tocando, num cartão embaixo dos ícones.</div></div>
  <div class="item"><div class="quando">3.3 · 21/11/2026</div><div class="titulo">Pular músicas rápido sem travar nem reiniciar</div><div class="texto">Com a capa do álbum aparecendo.</div></div>
  <div class="item"><div class="quando">3.2 · 18/11/2026</div><div class="titulo">Jogos</div><div class="texto">No menu Aplicativos: voar entre obstáculos, encaixar blocos e a <strong>Cobrinha</strong>.</div></div>
  <div class="item"><div class="quando">3.0 · 17/11/2026</div><div class="titulo">Menu Aplicativos</div><div class="texto">Na tela inicial, com Despertador e Imagem.</div></div>
  <div class="item"><div class="quando">2.2.1 · 16/11/2026</div><div class="titulo">Capas muito grandes não travam mais o player</div></div>
  <div class="item"><div class="quando">2.2 · 15/11/2026</div><div class="titulo">Ícones escuros com símbolos coloridos</div></div>
  <div class="item"><div class="quando">2.1 · 15/11/2026</div><div class="titulo">Ícones em grafite</div></div>
  <div class="item"><div class="quando">2.0 · 12/11/2026</div><div class="titulo">Capa do álbum</div><div class="texto">Na tela Tocando Agora.</div></div>
  <div class="item"><div class="quando">1.0 · 30/10/2026</div><div class="titulo">Atualizar por SD, logo e fundo preto</div><div class="texto">Barra superior com relógio, OpenPod e bateria, ícones novos com moldura, textos em português revisados.</div></div>
</div>

<h3>OpenPod RockBox</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">5.3 · 26/11/2026</div><div class="titulo">Nova numeração</div><div class="texto">O RockBox passa a <code>firmware.customização.compilação</code> (era 1.x), e volta os recursos do próprio sistema: <strong>Personalizar o menu principal</strong>, <strong>Tempo de reprodução</strong> e <strong>Limpar o disco</strong>.</div></div>
  <div class="item"><div class="quando">1.2 · 23/11/2026</div><div class="titulo">Mais estável e leve</div><div class="texto">Só o tema OpenPod e o padrão do Rockbox, sem os jogos e apps que travavam. Para limpar o cartão, instale com <strong>"Começar do zero"</strong>.</div></div>
  <div class="item"><div class="quando">1.1 · 23/11/2026</div><div class="titulo">Volume na tela</div><div class="texto">Ao aumentar ou baixar, a tela Tocando agora mostra a barra e o nível do volume.</div></div>
  <div class="item"><div class="quando">1.0 · 22/11/2026</div><div class="titulo">OpenPod RockBox</div><div class="texto">O Rockbox para o SL6801 com o tema OpenPod e 50 idiomas. <em>* Capa do álbum em beta</em></div></div>
</div>

<h3>OpenPod Tune (o programa)</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">0.4 · 26/11/2026</div><div class="titulo">StorePod</div><div class="texto">A lojinha dentro do Tune, com temas, apps e jogos testados. O primeiro item é o <strong>Tema OpenPod</strong>.</div></div>
  <div class="item"><div class="quando">0.2 · 23/11/2026</div><div class="titulo">OpenPod Tune</div><div class="texto">O instalador ganha o nome de Tune, e ganha o Linux. A janela se atualiza sozinha durante a instalação.</div></div>
</div>

<h3>Próximas versões (planejado)</h3>
<p><strong>As atualizações saem todo dia 10 de cada mês.</strong></p>
<table>
  <tr><td>RockBox 6.0 · previsto</td><td><strong>Capa do álbum</strong> no OpenPod RockBox, com os mesmos tamanhos aceitos no OpenPod System</td></tr>
  <tr><td>5.4 · 10/01/2027</td><td>Mais jogos: tênis, quebra-cabeça de números, jogo da memória, campo de minas e um bichinho virtual para cuidar</td></tr>
  <tr><td>5.5 · previsto</td><td>Jogos instalados pelo cartão SD e um kit aberto para a comunidade criar jogos</td></tr>
</table>
<p><small>A 3.4 é interna (estudo do firmware), não é lançada. Os planos podem mudar conforme os testes no aparelho.</small></p>'''

    en = '''<h2 id="history">History</h2>
<h3>OpenPod System</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">5.3 · 2026-11-26</div><div class="titulo">Renumbering of 3.5</div><div class="texto">Same features, new name: System moves to 5.x, to sit next to RockBox 5.x.</div></div>
  <div class="item"><div class="quando">3.5 · 2026-11-22</div><div class="titulo">Player on the home screen</div><div class="texto">The name of the playing song, in a card below the icons.</div></div>
  <div class="item"><div class="quando">3.3 · 2026-11-21</div><div class="titulo">Skipping songs fast without freezing or rebooting</div><div class="texto">With the album art showing.</div></div>
  <div class="item"><div class="quando">3.2 · 2026-11-18</div><div class="titulo">Games</div><div class="texto">In the Apps menu: flying between obstacles, fitting blocks and the <strong>Snake</strong>.</div></div>
  <div class="item"><div class="quando">3.0 · 2026-11-17</div><div class="titulo">Apps menu</div><div class="texto">On the home screen, with Alarm and Image.</div></div>
  <div class="item"><div class="quando">2.2.1 · 2026-11-16</div><div class="titulo">Very large covers no longer freeze the player</div></div>
  <div class="item"><div class="quando">2.2 · 2026-11-15</div><div class="titulo">Dark icons with colored symbols</div></div>
  <div class="item"><div class="quando">2.1 · 2026-11-15</div><div class="titulo">Graphite icons</div></div>
  <div class="item"><div class="quando">2.0 · 2026-11-12</div><div class="titulo">Album art</div><div class="texto">On the Now Playing screen.</div></div>
  <div class="item"><div class="quando">1.0 · 2026-10-30</div><div class="titulo">Update via SD, logo and black background</div><div class="texto">Top bar with clock, OpenPod and battery, new icons with a frame, revised Portuguese texts.</div></div>
</div>

<h3>OpenPod RockBox</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">5.3 · 2026-11-26</div><div class="titulo">New numbering</div><div class="texto">RockBox becomes <code>firmware.customization.build</code> (it used to be 1.x), and the system's own tools are back: <strong>Customize main menu</strong>, <strong>Playing time</strong> and <strong>Disk tidy</strong>.</div></div>
  <div class="item"><div class="quando">1.2 · 2026-11-23</div><div class="titulo">More stable and light</div><div class="texto">Only the OpenPod theme and the Rockbox default, without the games and apps that froze. To clean the card, install with <strong>"Start from scratch"</strong>.</div></div>
  <div class="item"><div class="quando">1.1 · 2026-11-23</div><div class="titulo">Volume on screen</div><div class="texto">When you turn it up or down, the Now Playing screen shows the bar and the volume level.</div></div>
  <div class="item"><div class="quando">1.0 · 2026-11-22</div><div class="titulo">OpenPod RockBox</div><div class="texto">Rockbox for the SL6801 with the OpenPod theme and 50 languages. <em>* Album art in beta</em></div></div>
</div>

<h3>OpenPod Tune (the program)</h3>
<div class="trilha">
  <div class="item destaque"><div class="quando">0.4 · 2026-11-26</div><div class="titulo">StorePod</div><div class="texto">The little shop inside Tune, with themes, apps and tested games. The first item is the <strong>OpenPod theme</strong>.</div></div>
  <div class="item"><div class="quando">0.2 · 2026-11-23</div><div class="titulo">OpenPod Tune</div><div class="texto">The installer is now called Tune, and gains Linux. The window refreshes itself during the install.</div></div>
</div>

<h3>Next versions (planned)</h3>
<p><strong>Updates ship on the 10th of every month.</strong></p>
<table>
  <tr><td>RockBox 6.0 · planned</td><td><strong>Album art</strong> in OpenPod RockBox, with the same sizes accepted in OpenPod System</td></tr>
  <tr><td>5.4 · 2027-01-10</td><td>More games: table tennis, number slide puzzle, memory game, minefield and a virtual pet to look after</td></tr>
  <tr><td>5.5 · planned</td><td>Games installed from the SD card and an open kit for the community to make games</td></tr>
</table>
<p><small>3.4 is internal (a firmware study), it is not released. Plans may change as we test on the device.</small></p>'''
    return pt, en


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="docs/index.html")
    ap.add_argument("--saida", default="docs/index_novo.html")
    a = ap.parse_args()

    html = Path(a.entrada).read_text(encoding="utf-8")
    img = imagens(html)
    faltando = [k for k in ("home", "system", "rockbox") if k not in img]
    if faltando:
        raise SystemExit(f"faltou as imagens: {faltando}")

    inicio_pt, inicio_en = painel_inicio(img)
    tune_pt, tune_en = painel_tune(img)
    rec_pt, rec_en = painel_recursos()
    comp_pt, comp_en = painel_compat()
    leg_pt, leg_en = painel_legacy()
    sobre_pt, sobre_en = painel_sobre()
    hist_pt, hist_en = painel_historico()

    menu = """<nav class="menu" aria-label="Seções">
  <a href="#inicio" data-p="inicio">Início</a>
  <a href="#tune" data-p="tune">OpenPod Tune</a>
  <a href="#instalar" data-p="instalar">Instalar</a>
  <a href="#recursos" data-p="recursos">Recursos</a>
  <a href="#compat" data-p="compat">Compatibilidade</a>
  <a href="#sobre" data-p="sobre">Sobre</a>
  <a href="https://github.com/zeroproj/OpenPod/issues">Suporte</a>
</nav>"""
    menu_en = """<nav class="menu" aria-label="Sections">
  <a href="#inicio" data-p="inicio">Home</a>
  <a href="#tune" data-p="tune">OpenPod Tune</a>
  <a href="#instalar" data-p="instalar">Install</a>
  <a href="#recursos" data-p="recursos">Features</a>
  <a href="#compat" data-p="compat">Compatibility</a>
  <a href="#sobre" data-p="sobre">About</a>
  <a href="https://github.com/zeroproj/OpenPod/issues">Support</a>
</nav>"""

    rodape = """<footer>OpenPod é um projeto independente, sem ligação com a Smartlink, a Shenju ou o fabricante do aparelho. Jogos e kit de apps baseados no <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>, de Dmitry Brant (MIT). <a href="#sobre">Créditos</a>. Use por sua conta e risco. Esta página distribui só os arquivos de atualização; o código-fonte não é público.</footer>"""
    rodape_en = """<footer>OpenPod is an independent project, with no connection to Smartlink, Shenju or the player's manufacturer. Games and app kit based on <a href="https://github.com/dbrant/SL6801_player">SL6801_player</a>, by Dmitry Brant (MIT). <a href="#about">Credits</a>. Use at your own risk. This page ships only the update files; the source code is not public.</footer>"""

    saida = f"""<!doctype html>
<html lang="pt-BR" data-lang="pt" data-aba="novo">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>OpenPod</title>
<meta name="description" content="OpenPod — o OpenPod Tune instala e atualiza o seu player de música (chip Smartlink SL6801): OpenPod System e OpenPod RockBox, com o visual OpenPod.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<script>{JS}</script>
</head>
<body>
<main>
<nav class="idioma" aria-label="Idioma / Language">
  <button type="button" data-l="pt" onclick="idioma('pt')">PT</button>
  <button type="button" data-l="en" onclick="idioma('en')">EN</button>
</nav>
<div lang="pt">
{menu}
<div data-painel="inicio">
{inicio_pt}
{hist_pt}
</div>
<div data-painel="tune">
{tune_pt}
</div>
<div data-painel="recursos">
{rec_pt}
</div>
<div data-painel="compat">
{comp_pt}
</div>
<div data-painel="sobre">
{sobre_pt}
{rodape}
</div>
<div data-painel="legacy">
{leg_pt}
</div>
</div>

<div lang="en">
{menu_en}
<div data-painel="inicio">
{inicio_en}
{hist_en}
</div>
<div data-painel="tune">
{tune_en}
</div>
<div data-painel="recursos">
{rec_en}
</div>
<div data-painel="compat">
{comp_en}
</div>
<div data-painel="sobre">
{sobre_en}
{rodape_en}
</div>
<div data-painel="legacy">
{leg_en}
</div>
</div>
</main>
</body>
</html>
"""
    Path(a.saida).write_text(saida, encoding="utf-8")
    print(f"gerado {a.saida} ({len(saida)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
