#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/opencv.hpp>

using std::placeholders::_1;

class DepthViewer : public rclcpp::Node
{
public:
    DepthViewer() : Node("depth_viewer_cpp")
    {
        sub_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
            "/depth_frame", 10,
            std::bind(&DepthViewer::callback, this, _1));

        pub_ = this->create_publisher<sensor_msgs::msg::Image>(
            "/depth_image", 10);

        width_ = 240;
        height_ = 180;

        RCLCPP_INFO(this->get_logger(), "Depth Viewer Node Started");
    }

private:
    rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr sub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_;

    int width_;
    int height_;

    void callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
    {
        if (msg->data.size() != width_ * height_)
        {
            RCLCPP_WARN(this->get_logger(), "Invalid data size");
            return;
        }

        // Convert ke cv::Mat
        cv::Mat depth(height_, width_, CV_32F, (void*)msg->data.data());

        // Replace NaN
        cv::Mat depth_clean;
        cv::patchNaNs(depth, 0);

        // Normalize ke 0–255
        cv::Mat depth_norm;
        cv::normalize(depth, depth_norm, 0, 255, cv::NORM_MINMAX, CV_8U);

        // Apply colormap
        cv::Mat depth_color;
        cv::applyColorMap(depth_norm, depth_color, cv::COLORMAP_JET);
        cv::flip(depth_color, depth_color, -1);

        // Convert ke ROS Image
        auto msg_img = cv_bridge::CvImage(
            std_msgs::msg::Header(),
            "bgr8",
            depth_color
        ).toImageMsg();

        pub_->publish(*msg_img);
    }
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DepthViewer>());
    rclcpp::shutdown();
    return 0;
}