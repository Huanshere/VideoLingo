import Link from 'next/link'
import { Button } from '@/components/ui/button'
import HeroVideoDialog from "@/components/ui/hero-video-dialog";
import Script from 'next/script'

interface HeroProps {
	title: string
	description: string
	videoSrc: string
}

export default function Hero({ title, description, videoSrc }: HeroProps) {
	return (
		<section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
			<div className="container mx-auto px-4 md:px-6">
				<div className="flex flex-col items-center text-center">
					<div className="space-y-4">
						<h1 className="text-6xl font-bold tracking-tight">{title}</h1>
						<p className="mx-auto max-w-[700px] text-lg">{description}</p>
					</div>
					<div className="flex space-x-4 mt-8">
						<Link href="https://videolingo.io">
							<Button className="rounded-lg" size="lg">
								Try Now for Free
							</Button>
						</Link>
						<Link href={'/docs/start'}>
							<Button variant="outline" size="lg" className="opacity-80">
								Go to Docs
							</Button>
						</Link>
					</div>
					{/* 视频演示组件 */}
					<div className="w-full max-w-6xl mt-16 mb-16">
						<HeroVideoDialog
							animationStyle="from-center"
							videoSrc={videoSrc}
							thumbnailSrc="/images/demo.png"
							thumbnailAlt="Hero Video"
						/>
					</div>
				</div>
			</div>
			<Script src="https://www.unpkg.com/@heyform-inc/embed@latest/dist/index.umd.js" />
		</section>
	)
}
