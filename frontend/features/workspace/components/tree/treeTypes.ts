export type TreeMoveTarget = {
  parentId: string | null;
  beforeNodeId: string | null;
};

export type TreeDropIndicatorState = TreeMoveTarget & {
  id: string;
};

export type WorkspaceTreeNode<TNode> = {
  children: TNode[];
  id: string;
  parent_id: string | null;
  title: string;
  type: string;
};

export type TreeCreateAction<TCreateType extends string> = {
  ariaLabel: (nodeTitle: string) => string;
  type: TCreateType;
};
