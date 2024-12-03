#iChannel0                                                                     \
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/718smiley.svg/480px-718smiley.svg.png"

// precision mediump float;

void main() {
  vec2 uv = (gl_FragCoord.xy / iResolution.xy);
  gl_FragColor = texture(iChannel0, uv);
}