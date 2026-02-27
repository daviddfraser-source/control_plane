declare module "react-trello" {
  import { CSSProperties, ComponentType } from "react";

  export interface Card {
    id: string;
    title?: string;
    label?: string;
    description?: string;
    metadata?: unknown;
    [key: string]: unknown;
  }

  export interface Lane {
    id: string;
    title: string;
    label?: string;
    cards: Card[];
    [key: string]: unknown;
  }

  export interface BoardData {
    lanes: Lane[];
  }

  export interface BoardProps {
    data: BoardData;
    draggable?: boolean;
    laneDraggable?: boolean;
    cardDraggable?: boolean;
    collapsibleLanes?: boolean;
    editable?: boolean;
    canAddLanes?: boolean;
    style?: CSSProperties;
    cardStyle?: CSSProperties;
    laneStyle?: CSSProperties;
    onDataChange?: (nextData: BoardData) => void;
    onCardClick?: (cardId: string, metadata: unknown, laneId: string) => void;
    [key: string]: unknown;
  }

  const Board: ComponentType<BoardProps>;
  export default Board;
}
