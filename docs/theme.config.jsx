import { useRouter } from 'next/router'
import { useConfig } from 'nextra-theme-docs'

const title = 'VideoLingo'

export default {
	logo: <span>{title}</span>,
	project: {
		link: 'https://github.com/Huanshere/VideoLingo',
	},
	footer: {
		text: <span>{new Date().getFullYear()} © {title}.</span>,
	},
	i18n: [
		{ locale: 'en-US', text: 'English' },
		{ locale: 'zh-CN', text: '中文' },
		{ locale: 'ja', text: '日本語' },
	],
	head: () => {
		const { asPath, defaultLocale, locale } = useRouter()
		const { frontMatter } = useConfig()
		const url = 'https://videolingo.io' + (defaultLocale === locale ? asPath : `/${locale}${asPath}`)

		return (
			<>
				<link rel="icon" type="image/png" href="/favicon-48x48.png" sizes="48x48" />
				<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
				<link rel="shortcut icon" href="/favicon.ico" />
				<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
				<link rel="manifest" href="/site.webmanifest" />
				<meta property="og:url" content={url} />
				<meta property="og:title" content={frontMatter.title || title} />
				<meta
					property="og:description"
					content={frontMatter.description || 'The next site builder'}
				/>
			</>
		)
	},
	useNextSeoProps() {
		const { asPath } = useRouter()
		if (asPath !== '/') {
			return {
				titleTemplate: `%s | ${title}`,
			}
		}
	},
}
