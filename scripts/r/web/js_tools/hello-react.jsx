import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";

function App() {
  const [username, setUsername] = useState("loading...");

  useEffect(() => {
    setUsername("Ross");
  });

  return <button>username: {username}</button>;
}

const root = document.createElement("div");
document.body.appendChild(root);
ReactDOM.render(<App />, root);
