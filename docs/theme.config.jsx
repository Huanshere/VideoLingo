import { useRouter } from 'next/router'

export default {
	logo: <span>VideoLingo</span>,
	project: {
		link: 'https://github.com/Huanshere/VideoLingo',
	},
	footer: {
		text: <span>{new Date().getFullYear()} © VideoLingo.</span>,
	},
	i18n: [
		{ locale: 'en-US', text: 'English' },
		{ locale: 'zh-CN', text: '中文' },
	],
	useNextSeoProps() {
		const { asPath } = useRouter()
		if (asPath !== '/') {
			return {
				titleTemplate: '%s | VideoLingo',
			}
		}
	},
}
