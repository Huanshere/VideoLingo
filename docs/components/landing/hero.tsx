import Link from 'next/link'
import { Button } from '@/components/ui/button'
import HeroVideoDialog from "@/components/ui/hero-video-dialog";

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
						<p className="mx-auto max-w-[700px] text-lg">{description}</p>
					</div>
					<div className="space-x-4 mt-8">
						<Link href={'/docs/start'}>
							<Button className="bg-[#C05F3C] hover:bg-[#C96442] rounded-lg" size="lg">
								Start
							</Button>
						</Link>
						<Link href={githubLink} target="_blank" passHref>
							<Button className="rounded-lg" size="lg">
								GitHub
							</Button>
						</Link>
					</div>
					{/* 新增视频演示组件 */}
					<div className="w-full max-w-6xl mt-16 mb-16">
						<HeroVideoDialog
							animationStyle="from-center"
							videoSrc={videoSrc}
							thumbnailSrc="/images/369750234-47d965b2-b4ab-4a0b-9d08-b49a7bf3508c.mp4_20240930_173826.986.jpg"
							thumbnailAlt="Hero Video"
						/>
					</div>
				</div>
			</div>
		</section>
	)
}
