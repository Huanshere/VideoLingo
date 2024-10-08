import Hero from '@/components/landing/hero'
import Features from '@/components/landing/features'
import Comments from '@/components/landing/comments'
import FAQ from '@/components/landing/faq'
import GitHubStats from '@/components/landing/github-stats'
import { useData } from 'nextra/data'

export const Stars = () => {
	const { stars } = useData()
	return <strong>{stars}</strong>
}

export const RecentStargazers = () => {
	const { recentStargazers } = useData()
	return recentStargazers
}

export default function Landing({ data }) {
	const { hero, features, comments, faq } = data

	return (
		<div className="flex flex-col min-h-screen">
			<main className="flex-1 bg-[#FAFAF8] dark:bg-zinc-900 text-[#141413] dark:text-gray-100">
				<Hero {...hero} />
				{features && <Features {...features} />}
				{comments && <Comments {...comments} />}
				<GitHubStats stars={<Stars />} recentStargazers={RecentStargazers()} />
				{faq && <FAQ {...faq} />}
			</main>
		</div>
	)
}
