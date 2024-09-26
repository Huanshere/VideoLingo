import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { CheckCircle, ArrowRight } from 'lucide-react'
import Hero from '@/components/landing/hero'
export default function Component() {
	return (
		<div className="flex flex-col min-h-screen">
			<main className="flex-1 bg-[#F5F4EF] text-[#3D3929]">
				<Hero
					title="VideoLingo: 连接世界的每一帧"
					description="全自动视频搬运工，生成 Netflix 品质的字幕！克隆自己的声音进行配音！"
					githubLink="https://github.com/Huanshere/VideoLingo"
					videoSrc="/videos/369750234-47d965b2-b4ab-4a0b-9d08-b49a7bf3508c.mp4"
				/>

				<section id="features" className="w-full py-24 md:py-32">
					<div className="container mx-auto px-4 md:px-6">
						<h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16">
							强大功能，释放创意
						</h2>
						<div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
							{/* 功能卡片 */}
							{[
								{
									title: '智能字幕分割',
									description:
										'使用 NLP 和 LLM 技术，精确分割字幕，确保每一句话都恰到好处。',
									icon: <CheckCircle className="h-10 w-10 text-primary" />,
								},
								{
									title: '上下文感知翻译',
									description:
										'智能术语知识库，实现上下文感知翻译，让每一句翻译都自然流畅。',
									icon: <ArrowRight className="h-10 w-10 text-primary" />,
								},
								{
									title: '三步翻译过程',
									description: '直接翻译 - 反思 - 改进，多重保障，确保翻译质量。',
									icon: <CheckCircle className="h-10 w-10 text-primary" />,
								},
								{
									title: '精确字幕对齐',
									description: '单词级字幕对齐，让每一个字都准确同步。',
									icon: <ArrowRight className="h-10 w-10 text-primary" />,
								},
								{
									title: '高质量配音',
									description: 'GPT-SoVits 技术支持的高质量个性化配音，让视频更具魅力。',
									icon: <CheckCircle className="h-10 w-10 text-primary" />,
								},
								{
									title: '开发者友好',
									description: '结构化文件设计，方便开发者自定义和扩展功能。',
									icon: <ArrowRight className="h-10 w-10 text-primary" />,
								},
							].map((feature, index) => (
								<Card key={index} className="n-card">
									<CardHeader>
										<div className="flex items-center space-x-4">
											{feature.icon}
											<CardTitle>{feature.title}</CardTitle>
										</div>
									</CardHeader>
									<CardContent>
										<p>{feature.description}</p>
									</CardContent>
								</Card>
							))}
						</div>
					</div>
				</section>

				<section className="w-full py-24 md:py-32">
					<div className="container mx-auto px-4 md:px-6">
						<h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16">
							他们都在用 VideoLingo
						</h2>
						<div className="grid gap-8 lg:grid-cols-3">
							<Card className="n-card">
								<CardContent className="p-6">
									<p className="text-lg mb-4">
										"VideoLingo
										彻底改变了我们的视频本地化流程。现在我们可以以前所未有的速度和质量制作多语言内容"
									</p>
									<p className="font-semibold">张三, CEO @ TechStart</p>
								</CardContent>
							</Card>
							<Card className="n-card">
								<CardContent className="p-6">
									<p className="text-lg mb-4">
										"作为一个独立创作者，VideoLingo
										让我能够轻松地将我的内容推广到全球观众。简直是游戏规则的改变者！"
									</p>
									<p className="font-semibold">李四, YouTuber</p>
								</CardContent>
							</Card>
							<Card className="n-card">
								<CardContent className="p-6">
									<p className="text-lg mb-4">
										"VideoLingo 的 AI
										配音功能令人惊叹。它为我们的教育视频增添了一个全新的维度。"
									</p>
									<p className="font-semibold">王五, 在线教育平台创始人</p>
								</CardContent>
							</Card>
						</div>
					</div>
				</section>

				<section id="faq" className="w-full py-24 md:py-32 mb-32">
					<div className="container mx-auto px-4 md:px-6">
						<h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16">
							常见问题
						</h2>
						<Accordion type="single" collapsible className="w-full max-w-3xl mx-auto">
							<AccordionItem value="item-1">
								<AccordionTrigger>VideoLingo 支持哪些视频格式？</AccordionTrigger>
								<AccordionContent>
									VideoLingo 支持大多数常见的视频格式，包括 MP4, AVI, MOV, WMV
									等。如果您有特殊格式需求，请联系我们的支持团队。
								</AccordionContent>
							</AccordionItem>
							<AccordionItem value="item-2">
								<AccordionTrigger>翻译和配音的质量如何保证？</AccordionTrigger>
								<AccordionContent>
									我们使用先进的 AI 技术结合人工审核来确保翻译的准确性。对于配音，我们的
									GP-SoVits 技术可以生成自然流畅的语音。
								</AccordionContent>
							</AccordionItem>
							<AccordionItem value="item-3">
								<AccordionTrigger>处理一个视频需要多长时间？</AccordionTrigger>
								<AccordionContent>
									处理时间取决于视频的长度和所需的服务。通常，一个 5
									分钟的视频完成翻译和配音大约需要 30 分钟。
								</AccordionContent>
							</AccordionItem>
							<AccordionItem value="item-4">
								<AccordionTrigger>可以自定义 VideoLingo 的功能吗？</AccordionTrigger>
								<AccordionContent>
									是的，VideoLingo 提供了灵活的 API
									和开发者文档，允许您根据需求进行自定义和集成。
								</AccordionContent>
							</AccordionItem>
						</Accordion>
					</div>
				</section>
			</main>
		</div>
	)
}
