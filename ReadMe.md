# OpenUSD Workbench

<table width="100%" style="border: none;">
<td width="50%" valign="top">

### 👋 Welcome!

This repository is a development environment and resource hub for learning and experimenting with **Pixar's OpenUSD**. This repository is designed to remove the setup friction with OpenUSD, providing a consistent, containerized environment with all the necessary tools.

The core philosophy is simple: **learn by doing**. I get straight to the point so you can spend less time reading and more time doing.
</td>

<td width="50%" valign="top">

### 📖 Explore Documentation

Explore the **📁 docs** folder where you can find documentation on what OpenUSD is, why it is used and how it works. A solid base you need before diving deep into the actual code / examples.

### 🚀 Explore Examples

Explore the **📁 examples** folder where you can find projects that show you how to do certain things in certain ways. For example, you can find Houdini VEX code to see how it works.

</td>
</table>

## 📖 OpenUSD Guide

- [Introduction To OpenUSD](./docs/usd/introduction.md)
- Terminology
  - [Primitives](./docs/usd/terminology/prims.md)
  - [Kind](./docs/usd/terminology/kind.md)
  - [Purpose](./docs/usd/terminology/purpose.md)
  - [Layers](./docs/usd/terminology/layers.md)
  - [Opinions and Overrides](./docs/usd/terminology/opinion_override.md)
  - [Composition Arcs](./docs/usd/terminology/composition_arc.md)
  - [Schemas](./docs/usd/terminology/schemas.md) 
- [Talks](./docs/usd/talks.md)
- [Sample Projects](./docs/usd/sample_projects.md)
- [Scripting](./docs/usd/scripting.md)

## 🚀 Quick Start: DevContainer (Linux & Docker)

This repository is setup with a **Docker DevContainer** using **Visual Studio Code** so you can easily work within a consistent coding environment. 2 devcontainers are available, one for C++ and one for Python-only, but you can use Python in the C++ devcontainer too! All tools you need are installed so you can get to work quickly without having the hassle to setup your environment. Ideal for learning and experimentation!

* **Zero-Config**: Get a C++ and Python-USD environment running in minutes.
* **Educational**: Practical examples that mirror the theory found in the docs.
* **Linux-First**: Leveraging a Linux Docker environment to ensure stability and compatibility with OpenUSD's core libraries.

How to get started:

1.  **Clone the repo** to your local machine (linux). Ubuntu 24.04 LTS is recommended.
2.  **Open in VS Code**: Ensure you have the *Dev Containers* extension installed.
3.  **Reopen in Container**: When prompted, click "Reopen in Container" (or run the command from the Command Palette).
4.  **Start Coding**: Tools like **Python 3** and **OpenUSD** are pre-installed and added to your path.

> [!TIP]
> New to linux, docker, git, devcontainers? No worries I got you covered with a guide to get you up to speed in no time!
> Checkout my **[Linux-Guide](https://github.com/BenjaminYde/Linux-Guide)** these topics: 

## 🤝 Contributing

Contributions, snippets and resources are welcome! Please feel free to open a PR or an issue.