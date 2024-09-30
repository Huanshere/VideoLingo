const withNextra = require('nextra')({
    theme: 'nextra-theme-docs',
    themeConfig: './theme.config.jsx',
})

const nextConfig = {
    images: {
        unoptimized: true
    },
    i18n: {
        locales: ['en-US', 'zh-CN', 'ja'],
        defaultLocale: 'zh-CN'
    }
}

module.exports = withNextra(nextConfig)

// If you have other Next.js configurations, you can pass them as the parameter:
// module.exports = withNextra({ /* other next.js config */ })
