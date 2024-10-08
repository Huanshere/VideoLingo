import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'

export interface FAQItem {
	question: string
	answer: string
}

interface FAQProps {
	items: FAQItem[]
	title: string
}

export default function FAQ({ items, title }: FAQProps) {
	return (
		<section id="faq" className="w-full py-24 md:py-32 mb-32">
			<div className="container mx-auto px-4 md:px-6">
				<h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-16">
					{title}
				</h2>
				<Accordion type="single" collapsible className="w-full max-w-3xl mx-auto">
					{items &&
						items.map((item, index) => (
							<AccordionItem key={`item-${index + 1}`} value={`item-${index + 1}`}>
								<AccordionTrigger>{item.question}</AccordionTrigger>
							<AccordionContent>{item.answer}</AccordionContent>
						</AccordionItem>
					))}
				</Accordion>
			</div>
		</section>
	)
}
