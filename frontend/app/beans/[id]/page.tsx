import { BeanDetailView } from "@/components/BeanDetailView";

type BeanDetailPageProps = {
  params: {
    id: string;
  };
};

export default function BeanDetailPage({ params }: BeanDetailPageProps) {
  return <BeanDetailView beanId={Number(params.id)} />;
}
