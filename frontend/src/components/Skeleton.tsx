import React from 'react';

interface SkeletonProps {
    className?: string;
    width?: string | number;
    height?: string | number;
    style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    className = '',
    width,
    height,
    style
}) => {
    return (
        <div
            className={`animate-pulse bg-[#242836] rounded ${className}`}
            style={{
                width: width,
                height: height,
                ...style
            }}
        />
    );
};
