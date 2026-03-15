import os
import subprocess
from distutils.dir_util import copy_tree

from _browser import open_url
from _code import append_code, patch_code, prepend_code, prepend_line
from _shutil import call_echo, cd, copy, mkdir, update_json
from utils.editor import open_code_editor
from utils.jsonutil import save_json
from utils.menu.actionmenu import ActionMenu
from utils.template import render_template_file

project_dir = os.path.expanduser(os.environ["JS_PROJECT_DIR"])

overwrite_existing_file = bool(os.environ.get("OVERWRITE_EXISTING_FILE"))


REACT_INDEX_JS = "src/hello-react.jsx"
SERVER_INDEX_JS = "src/server/index.js"
MODEL_DIR = "src/server/models"
INDEX_JS = "src/index.js"
TEMPLATE_DIR = os.getcwd() + "/js_tools"
THREEJS_INDEX_JS = "src/hello-three.js"


class JSToolsMenu(ActionMenu):
    @ActionMenu.action()
    def add_css_loader(self):
        add_packages(["style-loader", "css-loader"], dev=True)

        # Add babel-loader to webpack config
        append_code(
            "webpack.config.js",
            "rules: [",
            """{
              test: /\.css$/i,
              use: ["style-loader", "css-loader"],
            },""",
        )

    @ActionMenu.action()
    def add_webpack(self, index_js="src/index.js", build_dir="docs"):
        WEBPACK_CONFIG = "webpack.config.js"

        add_packages(
            ["webpack", "webpack-cli", "webpack-dev-server", "html-webpack-plugin"],
            dev=True,
        )

        # CSS loader
        add_packages(["style-loader", "css-loader", "file-loader"], dev=True)

        if not os.path.exists(WEBPACK_CONFIG) or overwrite_existing_file:
            render_template_file(
                TEMPLATE_DIR + "/webpack.config.js",
                WEBPACK_CONFIG,
                context={"index_js": index_js, "build_dir": build_dir},
            )

        if not os.path.exists(index_js):
            os.makedirs(os.path.dirname(index_js), exist_ok=True)
            # pathlib.Path(index_js).touch()

        add_script_to_package(
            "start",
            "webpack serve --mode development --devtool inline-source-map --hot",
        )
        add_script_to_package("build", "webpack")

        # webpack_start()

    @ActionMenu.action()
    def add_react(self, index_js=REACT_INDEX_JS):
        self.add_webpack(index_js=index_js)

        # # https://create-react-app.dev/docs/getting-started/
        # call_echo("yarn create react-app client")

        add_packages(["react", "react-dom"])

        # CSS loader
        add_packages(["style-loader", "css-loader"])

        # Babel: transcompile jsx
        add_packages(
            [
                "babel-loader",
                "@babel/core",
                "@babel/preset-env",
                "@babel/preset-react",
                "babel-plugin-react-html-attrs",  # transform class → className
            ],
            dev=True,
        )

        with open(".babelrc", "w") as f:
            f.write(
                """{
  "presets": ["@babel/preset-env", "@babel/preset-react"],
  "plugins": ["react-html-attrs"]
}
"""
            )

        # Add babel-loader to webpack config
        append_code(
            "webpack.config.js",
            "rules: [",
            """{
              test: /\.jsx?$/,
              exclude: /node_modules/,
              use: {
                loader: "babel-loader",
              },
            },""",
        )

        mkdir(os.path.dirname(index_js))
        if not os.path.exists(index_js) or overwrite_existing_file:
            render_template_file(TEMPLATE_DIR + "/hello-react.jsx", index_js)

        add_script_to_package(
            "client",
            "webpack serve --mode development --devtool inline-source-map --hot",
        )

    @ActionMenu.action()
    def add_react_starter(self):
        # https://github.com/react-boilerplate/react-boilerplate-cra-template
        call_echo(
            ["npx", "create-react-app", "--template", "cra-template-rb", "my-app"],
            shell=True,
        )

    @ActionMenu.action()
    def add_MERN_stack(self):
        self.add_react()
        self.add_express()
        self.add_mongodb()

        add_script_to_package("dev", 'concurrently "npm run server" "npm run client"')

        # add "dev" to run server and client concurrently
        add_packages(["concurrently"], dev=True)
        call_echo("npm run dev")

    @ActionMenu.action()
    def add_dat_gui(self):
        add_packages(["dat.gui"])

    @ActionMenu.action()
    def add_p5(self, index_js="src/index.js"):
        add_packages(["p5"])
        add_packages(["@types/matter-js"], dev=True)

        s = """import p5 from "p5";

const sketch = (p) => {
  let x = 100;
  let y = 100;

  p.setup = function () {
    p.createCanvas(700, 410);
  };

  p.draw = function () {
    p.background(0);
    p.fill(255);
    p.rect(x, y, 50, 50);
  };
};

new p5(sketch);
"""

        if not os.path.exists(index_js) or overwrite_existing_file:
            mkdir(os.path.dirname(index_js))
            with open(index_js, "w") as f:
                f.write(index_js)

    @ActionMenu.action()
    def add_react_bootstrap(self):
        add_packages(["bootstrap", "react-bootstrap", "react-bootstrap-icons"])

        # https://react-bootstrap.netlify.app/getting-started/introduction/
        prepend_line(REACT_INDEX_JS, "import 'bootstrap/dist/css/bootstrap.min.css';")

    @ActionMenu.action()
    def add_express(self):
        add_packages(["express"])
        add_packages(["nodemon"], dev=True)  # Monitor js changes and and hot reload

        # Package.json
        add_script_to_package("server", "nodemon src/server/index.js")

        # Server index.js
        if not os.path.exists(SERVER_INDEX_JS) or overwrite_existing_file:
            mkdir(os.path.dirname(SERVER_INDEX_JS))
            with open(SERVER_INDEX_JS, "w") as f:
                f.write(
                    """const express = require('express');
const os = require('os');

const app = express();

app.use(express.static('dist'));

app.get("/api/getUsername", (req, res) =>
  res.send({ username: os.userInfo().username })
);

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));
"""
                )

    @ActionMenu.action()
    def add_mongodb(self):
        add_packages(["mongoose"])

        mkdir(MODEL_DIR)
        with open(MODEL_DIR + "/contact.js", "w") as f:
            f.write(
                """const mongoose = require("mongoose");

module.exports.Contact = mongoose.model(
  "contact",
  mongoose.Schema({
    name: {
      type: String,
      required: true,
    },
    phone: String,
    createDate: {
      type: Date,
      default: Date.now,
    },
  })
);
"""
            )

        patch_code(
            SERVER_INDEX_JS,
            "^",
            """const mongoose = require("mongoose");
mongoose
  .connect("mongodb://localhost/test_db", { useNewUrlParser: true })
  .then(() => {
    console.log("Database connected.");
  })
  .catch((err) => console.log(err));
""",
            count=1,
        )

    @ActionMenu.action()
    def add_threejs(self):
        add_packages(["three", "@types/three"])

        os.makedirs(os.path.dirname(THREEJS_INDEX_JS), exist_ok=True)
        if not os.path.exists(THREEJS_INDEX_JS):
            render_template_file(TEMPLATE_DIR + "/hello-three.js", THREEJS_INDEX_JS)

        add_links()
        copy(TEMPLATE_DIR + "/main.css", "src/main.css", overwrite=False)
        write_file(
            "src/index.js",
            """import "./hello-three";
import "./links/links";
import "./main.css";""",
        )

    @ActionMenu.action()
    def add_tweakpane(self):
        # https://cocopon.github.io/tweakpane/getting-started/
        add_packages(
            [
                "tweakpane",
                "@tweakpane/core",  # optional typescript support
            ]
        )

    @ActionMenu.action()
    def add_typescript(self):
        add_packages(["typescript", "ts-loader"], dev=True)

        if not os.path.exists("tsconfig.json"):
            save_json(
                "tsconfig.json",
                {
                    "compilerOptions": {
                        "outDir": "./dist/",
                        "noImplicitAny": True,
                        "removeComments": True,
                        "module": "es6",
                        "target": "es5",
                        "jsx": "react",
                        "allowJs": True,
                        "moduleResolution": "node",
                    }
                },
            )

        append_code(
            "webpack.config.js",
            "rules: [",
            """{
              test: /\.tsx?$/,
              use: 'ts-loader',
              exclude: /node_modules/,
            },""",
        )

        prepend_code(
            "webpack.config.js",
            "output: {",
            """resolve: {
              extensions: ['.tsx', '.ts', '.js'],
            },""",
        )

    @ActionMenu.action()
    def add_matterjs(self, index_js="src/index.js"):
        add_packages(["matter-js"])
        add_packages(["@types/matter-js"])

        write_file(
            index_js,
            """import * as Matter from "matter-js";

var Engine = Matter.Engine,
    Render = Matter.Render,
    Runner = Matter.Runner,
    Bodies = Matter.Bodies,
    Composite = Matter.Composite;

var engine = Engine.create();

var render = Render.create({
    element: document.body,
    engine: engine
});

var boxA = Bodies.rectangle(400, 200, 80, 80);
var boxB = Bodies.rectangle(450, 50, 80, 80);
var ground = Bodies.rectangle(400, 610, 810, 60, { isStatic: true });

Composite.add(engine.world, [boxA, boxB, ground]);

Render.run(render);

// create runner
var runner = Runner.create();

// run the engine
Runner.run(runner, engine);
""",
        )

    @ActionMenu.action()
    def open_vscode(self):
        open_code_editor(os.getcwd())

    @ActionMenu.action()
    def add_fontawesome(self):
        add_packages(
            [
                "@fortawesome/fontawesome-svg-core",
                "@fortawesome/free-brands-svg-icons",
            ]
        )
        print(
            "See also: https://fontawesome.com/v5.15/how-to-use/javascript-api/setup/library"
        )

    @ActionMenu.action()
    def add_face_landmark_detection(self):
        add_packages(
            [
                "@tensorflow-models/face-landmarks-detection",
                "@tensorflow/tfjs-backend-webgl",
                "@tensorflow/tfjs-converter",
                "@tensorflow/tfjs-core",
            ]
        )

    @ActionMenu.action()
    def add_links(self):
        copy_tree(TEMPLATE_DIR + "/links", "src/links")

    @ActionMenu.action()
    def nextjs_create_app(self):
        call_echo(["yarn", "create", "next-app", os.getcwd()], shell=True)

    @ActionMenu.action()
    def nextjs_start_dev_server(self):
        open_url("http://localhost:3000/")
        call_echo(["yarn", "dev"], shell=True)

    @ActionMenu.action()
    def yarn_init(self):
        subprocess.check_call(["run_script", "r/web/init_yarn_package.sh"])

    @ActionMenu.action()
    def add_puppeteer(self):
        add_packages(["puppeteer"])

    @ActionMenu.action()
    def add_eslint(self):
        """
        https://eslint.org/docs/latest/user-guide/getting-started
        """
        update_json(
            ".vscode/settings.json",
            {
                "editor.formatOnSave": True,
                "editor.defaultFormatter": "esbenp.prettier-vscode",
                "editor.codeActionsOnSave": {"source.fixAll.eslint": True},
                "eslint.validate": ["javascript"],
            },
        )
        add_packages(
            [
                "@typescript-eslint/eslint-plugin",
                "@typescript-eslint/parser",
                "eslint",
                "eslint-config-airbnb",
                "eslint-config-airbnb-typescript",
                "eslint-config-standard-with-typescript",
                "eslint-plugin-import",
                "eslint-plugin-n",
                "eslint-plugin-promise",
            ],
            dev=True,
        )
        write_file(
            ".eslintrc.js",
            """module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: ['airbnb', 'airbnb-typescript'],
  overrides: [],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: './tsconfig.json',
  },
  rules: {},
};
""",
        )

        write_file(
            ".prettierrc",
            """{
  "printWidth": 100,
  "singleQuote": true,
  "trailingComma": "all"
}
""",
        )


if __name__ == "__main__":
    cd(project_dir)
    print("Project dir: %s" % project_dir)

    copy(TEMPLATE_DIR + "/LICENSE", "LICENSE", overwrite=False)

    JSToolsMenu().exec()
