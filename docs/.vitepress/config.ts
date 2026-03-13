import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Parsec",
  description:
    "Desktop OCR application that turns scanned documents and images into searchable PDFs",
  base: "/parsec/",

  head: [["link", { rel: "icon", type: "image/svg+xml", href: "/parsec/logo.svg" }]],

  themeConfig: {
    nav: [
      { text: "Guide", link: "/guide/getting-started" },
      { text: "GitHub", link: "https://github.com/getcauldron/parsec" },
    ],

    sidebar: [
      {
        text: "Guide",
        items: [
          { text: "Getting Started", link: "/guide/getting-started" },
          { text: "Usage", link: "/guide/usage" },
          { text: "Architecture", link: "/guide/architecture" },
          { text: "FAQ", link: "/guide/faq" },
          { text: "Contributing", link: "/guide/contributing" },
        ],
      },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/getcauldron/parsec" },
    ],

    footer: {
      message: "Released under the MIT License.",
      copyright: "Copyright © 2025 Cauldron",
    },
  },
});
