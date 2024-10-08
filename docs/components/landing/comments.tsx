import { Card, CardContent } from '@/components/ui/card'

type Comment = {
	content: string
	author: string
	title: string
}

type Props = {
	items: Comment[]
	title: string
}

export default function Comments({ items, title }: Props) {
	return (
		<section className="w-full py-24 md:py-32">
			<div className="container mx-auto px-4 md:px-6">
				<h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16">
					{title}
				</h2>
				<div className="grid gap-8 lg:grid-cols-3">
					{items &&
						items.map((comment, index) => (
							<Card key={index} className="n-card !bg-[#F0EFEA] dark:!bg-zinc-800 border-none dark:text-gray-100">
								<CardContent className="p-10">
									<p className="text-lg mb-4">"{comment.content}"</p>
									<p className="font-semibold">
										{comment.author}, {comment.title}
									</p>
								</CardContent>
							</Card>
						))}
				</div>
			</div>
		</section>
	)
}
