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
					<div className="space-x-4 mt-8">
						<Link href={'/docs/start'}>
							<Button className="bg-[#C05F3C] hover:bg-[#C96442] rounded-lg" size="lg">
								Start
							</Button>
						</Link>
						<div
							data-heyform-id="52QH8JAj"
							data-heyform-type="modal"
							data-heyform-custom-url="https://form-vl.zeabur.app/form/"
							data-heyform-size="large"
							data-heyform-open-trigger="click"
							data-heyform-open-delay="5"
							data-heyform-open-scroll-percent="30"
							data-heyform-trigger-background="#bbf7d0"
							data-heyform-trigger-text="请求演示"
							data-heyform-hide-after-submit="true"
							data-heyform-auto-close="5"
						>
							<button className="heyform__trigger-button" type="button" onClick={() => (window as any).HeyForm.openModal('52QH8JAj')}>
								请求演示
							</button>
						</div>
					</div>
					{/* 视频演示组件 */}
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
			<Script src="https://www.unpkg.com/@heyform-inc/embed@latest/dist/index.umd.js" />
		</section>
	)
}
