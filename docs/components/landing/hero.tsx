import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface HeroProps {
  title: string
  description: string
  githubLink: string
  videoSrc: string
}

export default function Hero({ title, description, githubLink, videoSrc }: HeroProps) {
	return (
		<section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
			<div className="container mx-auto px-4 md:px-6">
				<div className="flex flex-col items-center text-center">
					<div className="space-y-4">
						<h1 className="text-6xl font-bold tracking-tight">{title}</h1>
						<p className="mx-auto max-w-[700px] text-lg">
							{description}
						</p>
					</div>
					<div className="space-x-4 mt-8">
						<Link href={githubLink} target="_blank" passHref>
							<Button className="bg-[#C05F3C] hover:bg-[#C96442] rounded-lg" size="lg">GitHub</Button>
						</Link>
					</div>
					{/* 新增视频演示组件 */}
					<div className="w-full max-w-6xl mt-16 mb-16">
						<div className="aspect-video rounded-2xl overflow-hidden">
							<video className="w-full h-full object-cover" controls>
								<source src={videoSrc} type="video/mp4" />
								您的浏览器不支持视频标签。
							</video>
						</div>
					</div>
				</div>
			</div>
		</section>
	)
}
