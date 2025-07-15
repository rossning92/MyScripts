#iChannel0                                                                     \
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Awesome_Face.svg/600px-Awesome_Face.svg.png"

// precision mediump float;

void main() {
  vec2 uv = (gl_FragCoord.xy / iResolution.xy);
  gl_FragColor = texture(iChannel0, uv);
}