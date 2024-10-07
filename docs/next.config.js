import nextra from 'nextra'

const withNextra = nextra({
    theme: 'nextra-theme-docs',
    themeConfig: './theme.config.tsx',
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

export default withNextra(nextConfig)

// If you have other Next.js configurations, you can pass them as the parameter:
// module.exports = withNextra({ /* other next.js config */ })
