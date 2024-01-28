set -e

{{ include('r/web/add_tailwindcss_nextjs.sh') }}

# DaisyUI (based on Tailwind CSS)
yarn add -D daisyui@latest

if ! grep -q "daisyui" tailwind.config.ts; then
    sed -i -r 's/(plugins: \[)/\1require("daisyui")/' tailwind.config.ts
fi
