import "./links.css";

const links = document.createElement("div");
links.id = "links";
links.innerHTML =
  '<a href="https://github.com/rossning92/t-rex" target="_blank"><span class="icon-github"></span> Source</a> | rossning92';
document.body.append(links);
